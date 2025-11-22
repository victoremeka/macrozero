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


def format_diff(diff: str):
    lines = diff.split('\n')
    result = []
    line_counter = 0
    in_diff = False

    for line in lines:
        if line.startswith('@@'):
            line_counter = 0
            in_diff = True
            result.append(line)
        elif in_diff and line:
            line_counter += 1
            result.append(f"{line_counter}| {line}")
        else:
            result.append(line)
            if not line:  # Empty line ends diff section
                in_diff = False

    return '\n'.join(result)


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
        body = pr["title"] + "\n\n" + pr["body"] if pr["body"] is not None else pr["title"]
        pr_number = pr["number"]
        repo_owner = pr["base"]["user"]["login"]
        repo_name = payload["repository"]["name"]
        pr_url = pr["url"]
        commits_url = pr["commits_url"]

        diff = requests.get(
            pr_url,
            headers={
                "Authorization": f"Bearer {_installation_token()}",
                "Accept": "application/vnd.github.diff"
            },
        ).text

        diff = format_diff(diff)

        dump_to_json(diff, "diff", is_json=False) # Housekeeping

        if action in ("reopened", "opened", "synchronize"):
            resolve_pending_review(repo_name=repo_name, repo_owner=repo_owner, pr_number=pr_number, status="COMMENT")
            review = await call_agent(diff)
            
            submit_review(
                review,
                owner=repo_owner,
                repo=repo_name,
                pull_number=pr_number
            )
