import json
import os
from typing import Any
from google import genai
from google.genai import types
import requests
from integrations.github_client import _installation_token
import re


from .agent import call_agent


APP_TAG = r"@macrozeroai" # for v2 (mentions)

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY"),
)

def dump_to_json(payload, name, is_json=True):
    if is_json:
        with open(f"payloads/{name}.json", "w", encoding="utf-8") as file:
            json.dump(payload, fp=file, indent=2)
    else:
        with open(f"{name}.txt", "w", encoding="utf-8") as f:
            f.write(payload)

def embed(str:str):
    embeddings = client.models.embed_content(
        model="gemini-embedding-001",
        contents=str,
        config=types.EmbedContentConfig(output_dimensionality=768),
    ).embeddings

    if embeddings:
        return embeddings[0].values

def submit_review(data: str, owner, repo, pull_number):
    review = requests.post(
        url=f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}/reviews",
        headers={
        "Accept": "application/vnd.github+json",
        "Authorization" :f"Bearer {_installation_token()}",
        },
        data={
            "body": data,
            "event":"COMMENT", # REQUEST_CHANGES, APPROVE, COMMENT (must always be one of these)
        }
    )
    print(review.headers)
    print(review.status_code, review.text)

def get_commit_diffs(commits_url, repo_owner, repo_name):
    pr_commits = requests.get(
        commits_url,
        headers={
            "Authorization": f"Bearer {_installation_token()}",
        }
    ).json()
    responses = []
    for commit in pr_commits:
        commit_sha = commit["sha"]

        response = requests.get(
            f"https://api.github.com/repos/{repo_owner}/{repo_name}/commits/{commit_sha}",
            headers={
                "Authorization": f"Bearer {_installation_token()}",
                "Accept": "application/vnd.github.diff"
            },
        ).text

        responses.append(response)

    return responses


def format_diff(diff: str):
    diff_split = diff.splitlines()
    at_positions = []
    commits = []
    for i, line in enumerate(diff_split):
        if re.search(r"^(@@).+(@@)$", line):
            at_positions.append(i-1)

    for i, pos in enumerate(at_positions):
        if i == len(at_positions)-1:
            commits.append(
                diff_split[pos+1: ]
            )
            break
        commits.append(
            diff_split[pos+1: at_positions[i+1]+1]
        )
    # dump_to_json(json.loads(commits), "formatted-diff", is_json=False)
    return commits

def resolve_pending_review(repo_owner, repo_name, pr_number, status):
    check_pending = requests.get(
        f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls/{pr_number}/reviews",
            headers={
                "Authorization": f"Bearer {_installation_token()}",
            },
        ).json()
    for review in check_pending:
        if review["state"] == "PENDING":
            x = requests.post(
                f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls/{pr_number}/reviews/{review["id"]}/events",
                headers={
                    "Authorization": f"Bearer {_installation_token()}",
                },
                json={
                    "event": status,
                }
            ).json()

async def handle_pull_request(payload: dict[str, Any]):
    # find @ tag -> ^(@@).+(@@)$
    # diff start -> ^(diff)
    dump_to_json(payload, "pr")

    pr = payload.get("pull_request")

    if pr:
        action = payload["action"]
        body = pr["title"] + "\n\n" + pr["body"]
        pr_number = pr["number"]
        repo_owner = pr["base"]["user"]["login"]
        repo_name = payload["repository"]["name"]
        pr_url = pr["url"]
        commits_url = pr["commits_url"]

        diff = get_commit_diffs(commits_url=commits_url, repo_owner=repo_owner, repo_name=repo_name)
        dump_to_json(diff, "diff",) # Housekeeping
        # diff = format_diff(body + "\n\n" + diff)

        if action in ("reopened", "opened", "synchronize"):
            resolve_pending_review(repo_name=repo_name, repo_owner=repo_owner, pr_number=pr_number, status="COMMENT")

            # submit_review(
            #     "Hello from macrozeroai! 🥳",
            #     owner=repo_owner,
            #     repo=repo_name,
            #     pull_number=pr_number
            # )
            # await call_agent(diff)
