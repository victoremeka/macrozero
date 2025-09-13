from integrations.github_client import *
# from services.github_sync import dump_to_json
from typing import Literal


def create_pr_review(owner: str, repo: str, number: int, body: str, comments: list[dict], event: Literal["COMMENT","REQUEST_CHANGES","APPROVE"] = "COMMENT"):

    payload = {
        "body": body,
        "event": event,
        "comments": comments,  # each item must include: path, body, side ("RIGHT"), and position or line
    }

    resp = gh_json(
        method="post",
        path=f"/repos/{owner}/{repo}/pulls/{number}/reviews",
        json=payload,
        headers={"Accept": "application/vnd.github+json"},
    )
    return resp