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

def handle_pull_request(payload: dict):
    action = payload.get("action")
   
    if action in {"opened", "reopened", "synchronize"}:
        pr : dict = payload["pull_request"]
        repo_owner = pr["base"]["repo"]["owner"]["login"]
        repo_name = pr["base"]["repo"]["name"]
        repo_id = pr["base"]["repo"]["id"]
        number = pr["number"]
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
            upsert_pr(
                session=session,
                repo=repo,
                number=number,
                state=state,
                text=text,
                embedding=embedding,
            )
            session.commit()
            session.close()
            comment_on_pr(repo_owner, repo_name, number, "👋 Automation acknowledged this pull request.")

        except SQLAlchemyError as e:
            print("Database error:", e)

    return {"status": "ok", "action": action}

def handle_issue(payload : dict):
    action = payload.get("action")

    if action in {"opened", "reopened"}:
        # Activate Agent Orchestrator
        pass