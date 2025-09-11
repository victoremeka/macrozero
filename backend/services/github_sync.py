import json
import re

from sqlmodel import select, Session
from integrations.github_client import *
from models import *
from sqlalchemy.exc import SQLAlchemyError
from tidb_vector.sqlalchemy  import VectorType

import lmstudio as lms #TODO: take out in prod.

from db import (
    upsert_repo,
    upsert_pr,
    upsert_commit,
    upsert_review,
    upsert_issue,
    link_commit_to_pr,
    link_issue_file,
)


def dump_to_json(name, data):
    with open(f"test/{name}.json", "w") as f:
        json.dump(data, f, indent=2)

def add_pr_commits_to_db(pr: PullRequest, repo: Repository, repo_name: str, owner: str, number: int, session: Session):
    model = lms.embedding_model("nomic-embed-text-v1.5")

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
            diff_embedding=model.embed(out), # type: ignore
        )
        link_commit_to_pr(
            session=session,
            commit=commit,
            pr=pr
        )

def handle_pull_request(payload: dict, session: Session):
    action = payload.get("action")
    pr : dict = payload["pull_request"]
    repo_owner = pr["base"]["repo"]["owner"]["login"]
    repo_name = pr["base"]["repo"]["name"]
    repo_id = pr["base"]["repo"]["id"]
    number = pr["number"]
    head_branch = pr["head"]["ref"]
    base_branch = pr["base"]["ref"]

    if pr.get("body"):
        text = pr["title"] + " ".join(re.split(r"\n|\r", pr["body"].strip()))
    else:
        text = pr["title"]
    
    model = lms.embedding_model("nomic-embed-text-v1.5")
    embedding = model.embed(text)

    repo = upsert_repo(
        session=session,
        gh_id=repo_id,
        owner=repo_owner,
    )

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
        # dump_to_json("webhook_pr_closed_response", payload)
        pullrequest = session.exec(select(PullRequest).where(PullRequest.repo_id == repo.id, PullRequest.number == number)).one_or_none()

        if pullrequest:
            pullrequest.state = PRState.CLOSED
            session.add(pullrequest)
            session.flush()
            session.refresh(pullrequest)
    
    elif action == "merged":
        pullrequest = session.exec(select(PullRequest).where(PullRequest.repo_id == repo.id, PullRequest.number == number)).one_or_none()

        if pullrequest:
            pullrequest.state = PRState.MERGED
            session.add(pullrequest)
            session.flush()
            session.refresh(pullrequest)

    # TODO: Activate Agent Orchestrator
    return {"status": "ok", "action": action}

def handle_pull_request_review(payload: dict, session: Session):
    action = payload.get("action")
    review = payload["review"]
    repo = payload["repository"]

    pr_number = payload["pull_request"]["number"]

    repo_db = session.exec(select(Repository).where(Repository.gh_id == repo["id"])).one()
    pr_db = session.exec(select(PullRequest).where(PullRequest.repo_id == repo_db.id, PullRequest.number == pr_number)).one()
    
    review_id = review["id"]
    author_login = review["user"]["login"]
    comment_text = review["body"]
    review_type = review["state"]

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
            created_at=datetime.now(timezone.utc)
        )
    except SQLAlchemyError as e:
        print("Database error:", e)

def handle_pull_request_review_comment(payload: dict, session: Session):
    action = payload.get("action")
    comment = payload["comment"]
    repo = payload["repository"]

    pr_number = payload["pull_request"]["number"]

    repo_db = session.exec(select(Repository).where(Repository.gh_id == repo["id"])).one()
    pr_db = session.exec(select(PullRequest).where(PullRequest.repo_id == repo_db.id, PullRequest.number == pr_number)).one()

    comment_id = comment["id"]
    review_id = comment["pull_request_review_id"]
    author_login = comment["user"]["login"]
    comment_text = comment["body"]
    file_path = comment["path"]
    line_number = comment["line"]
    review_type = "INLINE"

    try:
        review = upsert_review(
            session=session,
            pr=pr_db,
            comment_id=comment_id,
            review_id=review_id,
            author_login=author_login,
            file_path=file_path,
            comment_text=comment_text,
            review_type=review_type,
            line_number=line_number,
            created_at=datetime.now(timezone.utc)
        )
    except SQLAlchemyError as e:
        print("Database error:", e)

def handle_pull_request_review_thread(payload: dict, session: Session):
    pass

def handle_issue(payload : dict, session: Session):
    action = payload.get("action")

    if action in {"opened", "reopened"}:
        # Activate Agent Orchestrator
        pass