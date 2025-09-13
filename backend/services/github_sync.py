import json
import re

from sqlmodel import select, Session
from integrations.github_client import *
from models import *
from sqlalchemy.exc import SQLAlchemyError
from tidb_vector.sqlalchemy  import VectorType

from db import (
    upsert_repo,
    upsert_pr,
    upsert_commit,
    upsert_review,
    upsert_issue,
    link_commit_to_pr,
    link_issue_file,
)
import lmstudio as lms #TODO: take out in prod.

model = lms.embedding_model("nomic-embed-text-v1.5") # TODO take out in prod

def dump_to_json(name, data):
    with open(f"test/{name}.json", "w") as f:
        json.dump(data, f, indent=2)

def add_pr_commits_to_db(pr: PullRequest, repo: Repository, repo_name: str, owner: str, number: int, session: Session):
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

def handle_pull_request(payload: dict, session: Session, repo: Repository):
    action = payload.get("action")
    pr : dict = payload["pull_request"]
    repo_owner = pr["base"]["repo"]["owner"]["login"]
    repo_name = pr["base"]["repo"]["name"]
    number = pr["number"]
    head_branch = pr["head"]["ref"]
    base_branch = pr["base"]["ref"]

    if pr.get("body"):
        text = pr["title"] + " ".join(re.split(r"\n|\r", pr["body"].strip()))
    else:
        text = pr["title"]
    
    embedding = model.embed(text)

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

def handle_pull_request_review(payload: dict, session: Session, repo: Repository):
    action = payload.get("action")
    review = payload["review"]

    pr_number = payload["pull_request"]["number"]

    pr_db = session.exec(select(PullRequest).where(PullRequest.repo_id == repo.id, PullRequest.number == pr_number)).one()
    
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

def handle_pull_request_review_comment(payload: dict, session: Session, repo: Repository):
    comment = payload["comment"]

    pr_number = payload["pull_request"]["number"]

    pr_db = session.exec(select(PullRequest).where(PullRequest.repo_id == repo.id, PullRequest.number == pr_number)).one()

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

def handle_issue(payload : dict, session: Session, repo: Repository):
    action = payload.get("action")
    issue = payload["issue"]
    issue_number = issue["number"]
    issue_state = IssueState.OPEN
    repo_id = payload["repository"]["id"]
    

    content = f"""
    title: {issue["title"]}
    body: {issue["body"].strip()}
    """
    
    if action in {"opened", "edited", "closed"}:
        if issue_state == "closed":
            issue_state = IssueState.CLOSED
        try:
            upsert_issue(
                session=session,
                repo=repo.id,
                number=issue_number,
                state=issue_state,
                content_embedding=model.embed(content) # type: ignore
            )
        except SQLAlchemyError as e:
            print(f"Database error:", e)
    elif action == "deleted":
        try:
            issue = session.exec(select(Issue).where(Issue.repo_id == repo.id, Issue.number == issue_number)).one_or_none()

            if issue:
                session.delete(issue)
                session.flush()
        except SQLAlchemyError as e:
            print("Database Error:", e)
    else:
        print("Error: repository does not exist")