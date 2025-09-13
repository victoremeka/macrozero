from integrations.github_client import *
from services.github_sync import dump_to_json


def create_pr_review(owner: str, repo: str, number: int, body:str, comments: list[dict]):
    diff = get_pull_request_diff(owner=owner, repo=repo, number=number)

    dump_to_json(
        name="payload_response",
        data=diff
    )
    
    resp = gh_json(
        method="post",
        path=f"repos/{owner}/{repo}/pulls/{number}/reviews",
        json={
            "body" : body,
            "comments" : comments
        }
    )

