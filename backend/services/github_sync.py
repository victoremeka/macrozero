import json
import re
from integrations.github_client import *
from models import *
from sqlalchemy.exc import SQLAlchemyError
from tidb_vector.sqlalchemy  import VectorType

import lmstudio as lms #TODO: take out in prod.

from db import (
    upsert_repo,
    upsert_pr,
    upsert_commit,
    upsert_issue,
    link_commit_to_pr,
    link_issue_file,
    get_session
)
session = get_session()

def add_pr_commits_to_db(repo: Repository, repo_name: str, owner: str, number: int,):
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


def handle_pull_request(payload: dict):
    action = payload.get("action")
   
    if action in {"opened", "reopened", "synchronize"}:
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
        state = PRState.OPEN

        model = lms.embedding_model("nomic-embed-text-v1.5")
        embedding = model.embed(text)
        try:
            # Activate Agent Orchestrator
            repo = upsert_repo(
                session=session,
                gh_id=repo_id,
                owner=repo_owner,
            )
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
            add_pr_commits_to_db(repo, repo_name, repo_owner, number)
            session.commit()
            session.close()

        except SQLAlchemyError as e:
            print("Database error:", e)

    return {"status": "ok", "action": action}

def handle_pull_request_review(payload: dict):
    pass

def handle_pull_request_review_comment(payload: dict):
    pass

def handle_pull_request_review_thread(payload: dict):
    pass

def handle_issue(payload : dict):
    action = payload.get("action")

    if action in {"opened", "reopened"}:
        # Activate Agent Orchestrator
        pass