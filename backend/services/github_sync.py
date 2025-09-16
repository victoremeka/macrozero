"""Utilities for synchronizing GitHub webhook events with the database and agents.

This module consumes GitHub webhook payloads and:
- Upserts repositories, pull requests, commits, reviews, and issues into TiDB via SQLModel
- Enriches data with embeddings
- Invokes the agent orchestrator to perform PR reviews

Functions are organized by webhook type (pull_request, pull_request_review, issues) and
helpers for commit ingestion and small utilities (e.g., JSON dumping for debug).
"""

import json
import re
from sqlmodel import select, Session
from integrations.github_client import *
from models import *
from sqlalchemy.exc import SQLAlchemyError
from services.agent_orchestrator import call_agent_async
from datetime import datetime, timezone
from pytidb import TiDBClient
from google import genai
from google.genai import types
import os, dotenv

dotenv.load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY"),
)

def embed(str):
    return client.models.embed_content(
        model="gemini-embedding-001",
        contents=str,
        config=types.EmbedContentConfig(output_dimensionality=768),
    ).embeddings


from db import (
    upsert_repo,
    upsert_pr,
    upsert_commit,
    upsert_review,
    upsert_issue,
    link_commit_to_pr,
    link_issue_file,
)

def dump_to_json(name: str, data) -> None:
    """Write arbitrary data to a JSON file under test/ for debugging.

    Args:
        name: Base file name (without directory); `.json` is appended and placed under `test/`.
        data: Any JSON-serializable object to persist.

    Returns:
        None. Writes/overwrites `test/{name}.json` on disk.

    Notes:
        Intended for local debugging and snapshotting webhook payloads or intermediate state.
    """
    with open(f"test/{name}.json", "w") as f:
        json.dump(data, f, indent=2)

def add_pr_commits_to_db(
    pr: PullRequest,
    repo: Repository,
    repo_name: str,
    owner: str,
    number: int,
    session: Session,
) -> None:
    """Ingest commits for a pull request and persist them with embeddings.

    Fetches all commits for the given PR, assembles lightweight textual context
    (commit sha, message, and per-file non-hunk-header lines), generates an
    embedding for each commit, upserts the commit rows, and links them to the PR.

    Args:
        pr: The database PullRequest row to link commits to.
        repo: The database Repository row owning the PR.
        repo_name: Repository name (e.g., "macrozero").
        owner: Repository owner/org login.
        number: Pull request number.
        session: Open SQLModel session used for persistence.

    Returns:
        None. Mutates the database session (insert/update rows and links).

    Side effects:
        - Network calls to GitHub to list PR commits.
        - Embedding computation for commit context.
        - DB writes for commits and link table.
    """
    commits = list_pr_commits(
        repo_name=repo_name,
        owner=owner,
        number=number
    )

    for commit in commits:
        msg=commit["commit"]["message"]

        out = [f"Commit: {commit.get('sha','')}", f"Message: {msg}"]
        for f in commit.get("files", []):
            if "patch" not in f:
                continue
            lines = [l for l in f["patch"].splitlines() if not l.startswith("@@")]
            out.append(f"\nFile: {f['filename']}\n" + "\n".join(lines))
        out = "\n".join(out)

        commit = upsert_commit(
            session=session,
            repo=repo,
            sha=commit["sha"],
            message=msg,
            author_login=commit["author"]["login"],
            diff_embedding=embed(out), # type: ignore
        )
        link_commit_to_pr(
            session=session,
            commit=commit,
            pr=pr
        )

async def handle_pull_request(payload: dict, session: Session, repo: Repository) -> dict:
    """Handle GitHub pull_request webhooks and synchronize state.

    Processes actions: opened, reopened, synchronize, edited, closed.
    - For open/reopen/synchronize: upserts PR record, embeds PR text, ingests commits,
      and triggers the agent orchestrator to review the PR using diff + metadata.
    - For edited: updates cached text/branch fields.
    - For closed: records CLOSED or MERGED state.

    Args:
        payload: Full webhook JSON payload.
        session: Active SQLModel session for persistence.
        repo: Database Repository row corresponding to payload["repository"].

    Returns:
        A short status dictionary, e.g., {"status": "ok", "action": <action>} for logging/callsites.

    Notes:
        - Embeddings are generated via the configured local model in dev.
        - Network calls are made to GitHub to retrieve the PR diff and commits.
    """
    action = payload.get("action")
    pr : dict = payload["pull_request"]
    repo_owner = pr["base"]["repo"]["owner"]["login"]
    repo_name = pr["base"]["repo"]["name"]
    number = pr["number"]
    title = pr["title"]
    head_branch = pr["head"]["ref"]
    base_branch = pr["base"]["ref"]


    if pr.get("body"):
        text = "title: " + pr["title"] + " body: " + " ".join(re.split(r"\n|\r", pr["body"].strip()))
    else:
        text = "title: " + pr["title"]
    
    embedding = embed(text)

    diff = get_pull_request_diff(owner=repo_owner, repo=repo_name, number=number)

    if action in {"opened", "reopened", "synchronize"}:
        state = PRState.OPEN
        try:
            pullrequest = upsert_pr(
                session=session,
                repo=repo,
                number=number,
                state=state,
                text=text,
                embedding=embedding, # type: ignore
                head_branch=head_branch,
                base_branch=base_branch,
            )
            add_pr_commits_to_db(pullrequest, repo, repo_name, repo_owner, number, session)
            await call_agent_async(
                payload={
                    "type": "pull_request",
                    "diff": diff,
                    "owner": repo_owner,
                    "repo": repo_name,
                    "number": number,
                    "body": text
                },
                user_id=repo_owner,
                session_id=str(pr["id"]),
            )
        except SQLAlchemyError as e:
            print("Database error:", e)

    elif action == "edited":
        pullrequest = session.exec(select(PullRequest).where(PullRequest.repo_id == repo.id, PullRequest.number == number)).one_or_none()

        if pullrequest:
            pullrequest.text = text
            pullrequest.base_branch = base_branch
            session.add(pullrequest)
            session.flush()
            session.refresh(pullrequest)
    
    elif action == "closed":
        pullrequest = session.exec(select(PullRequest).where(PullRequest.repo_id == repo.id, PullRequest.number == number)).one_or_none()

        if pullrequest:
            pullrequest.state = PRState.MERGED if pr.get("merged") else PRState.CLOSED  # merged handled here
            session.add(pullrequest)
            session.flush()
            session.refresh(pullrequest)

    return {"status": "ok", "action": action}

def handle_pull_request_review(payload: dict, session: Session, repo: Repository) -> None:
    """Persist a PR review event (approve/comment/request_changes) into the database.

    On dismissal, removes the stored review. Otherwise, upserts the review row with
    author, body, type, and timestamp.

    Args:
        payload: Full webhook JSON payload for pull_request_review.
        session: Active SQLModel session for persistence.
        repo: Database Repository row corresponding to payload["repository"].

    Returns:
        None. Commits are performed by the caller after processing the event.
    """
    action = payload.get("action")
    review = payload["review"]

    pr_number = payload["pull_request"]["number"]

    pr_db = session.exec(select(PullRequest).where(PullRequest.repo_id == repo.id, PullRequest.number == pr_number)).one_or_none()
    
    review_id = review["id"]
    author_login = review["user"]["login"]
    comment_text = review["body"]
    review_type = review["state"]
    submitted_at = review.get("submitted_at")

    if pr_db:
        if action == "dismissed":
            r = session.exec(select(Review).where(Review.pr_id == pr_db.id, Review.review_id == review_id)).one()
            session.delete(r)
            session.flush()

        try:
            upsert_review(
                session=session,
                pr=pr_db,
                review_id=review_id,
                comment_text=comment_text,
                author_login=author_login,
                review_type=review_type,
                created_at=datetime.fromisoformat(submitted_at.replace("Z", "+00:00")) if submitted_at else datetime.now(timezone.utc),
            )
        except SQLAlchemyError as e:
            print("Database error:", e)
            session.rollback()

def handle_pull_request_review_comment(payload: dict, session: Session, repo: Repository) -> None:
    """Ignore individual review comment events.

    Inline review comments are intentionally not persisted to avoid duplicates and
    excessive row counts. The summary review records are stored in
    `handle_pull_request_review` instead.

    Args:
        payload: Full webhook JSON payload for pull_request_review_comment.
        session: Active SQLModel session (unused).
        repo: Database Repository row (unused).

    Returns:
        None.
    """
    return

def handle_issue(payload: dict, session: Session, repo: Repository) -> None:
    """Handle GitHub issues webhooks and synchronize a minimal issue index.

    Processes actions: opened, edited, closed, deleted. Upserts or deletes issue rows
    with a lightweight embedding of the title/body for later search/triage.

    Args:
        payload: Full webhook JSON payload for issues.
        session: Active SQLModel session for persistence.
        repo: Database Repository row corresponding to payload["repository"].

    Returns:
        None. The caller is responsible for committing the transaction.
    """
    action = payload.get("action")
    issue = payload["issue"]
    issue_number = issue["number"]

    gh_state = issue.get("state", "").lower()
    issue_state = IssueState.CLOSED if gh_state == "closed" or action == "closed" else IssueState.OPEN

    title = issue.get("title", "")
    body = issue.get("body", "")
    content = f"title: {title}\nbody: {body}"

    if action in {"opened", "edited", "closed"}:
        try:
            upsert_issue(
                session=session,
                repo=repo,
                number=issue_number,
                state=issue_state,
                content_embedding=embed(content),  # type: ignore
            )
        except SQLAlchemyError as e:
            print("Database error:", e)
    elif action == "deleted":
        try:
            issue_db = session.exec(select(Issue).where(Issue.repo_id == repo.id, Issue.number == issue_number)).one_or_none()
            if issue_db:
                session.delete(issue_db)
                session.flush()
        except SQLAlchemyError as e:
            print("Database error:", e)
    else:
        print(f"Ignored issue action: {action}")