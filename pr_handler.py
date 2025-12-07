import json
import os
import re
from typing import Any
from google import genai
from google.genai import types
import requests
from integrations.github_client import _installation_token
from base64 import b64decode


from agents.agent import call_agent


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

def submit_review(data : dict, owner, repo, pull_number, installation_token):
    review = requests.post(
        url=f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}/reviews",
        headers={
        "Accept": "application/vnd.github+json",
        "Authorization" :f"Bearer {installation_token}",
        },
        json = data
    )
    if not review.ok:
        print(f"{review.status_code} : review could not be submitted")
        print(review.content)
        print(review.headers)

def format_diff(diff: str):
    lines = diff.split('\n')
    result = []
    line_counter = 0
    in_diff = False
    hunk_start = False
    for line in lines:
        if line.startswith('diff --git'):
            in_diff = False
            line_counter = 0
            hunk_start = False
        elif line.startswith("@@") and not hunk_start:
            in_diff = True
            result.append(line)
            hunk_start = True
            continue

        if not in_diff:
            result.append(line)
            continue


        if in_diff:
            line_counter += 1
            result.append(f"{line_counter} | {line}")
        else:
            result.append(line)
    return '\n'.join(result)

def resolve_pending_review(repo_owner, repo_name, pr_number, status, installation_token):

    check_pending = requests.get(
        f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls/{pr_number}/reviews",
            headers={
                "Authorization": f"Bearer {installation_token}",
            },
        ).json()
    for review in check_pending:
        if review["state"] == "PENDING":
            x = requests.post(
                f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls/{pr_number}/reviews/{review["id"]}/events",
                headers={
                    "Authorization": f"Bearer {installation_token}",
                },
                json={
                    "event": status,
                }
            ).json()

def get_pr_files(repo_owner, repo_name, number, installation_token) -> str:

    headers={
        "Authorization": f"Bearer {installation_token}",
    }

    files = requests.get(
        url=f" https://api.github.com/repos/{repo_owner}/{repo_name}/pulls/{number}/files",
        headers=headers
    ).json()

    res = ""
    for f in files:
        path = f["filename"]

        f_content = requests.get(
            url=f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{path}",
            headers=headers
        ).json()["content"]
        content = b64decode(f_content).decode()

        res += f"filename: {path}\ncontent:\n{content}\n\n"
    return res

async def handle_pull_request(payload: dict[str, Any]):

    pr = payload.get("pull_request")

    if pr:
        action = payload["action"]
        body = pr["title"] + "\n\n" + pr["body"] if pr["body"] is not None else pr["title"]
        pr_number = pr["number"]
        repo_owner = pr["base"]["user"]["login"]
        repo_name = payload["repository"]["name"]
        pr_url = pr["url"]
        installation_token = _installation_token(owner=repo_owner, repo=repo_name)

        diff = requests.get(
            pr_url,
            headers={
                "Authorization": f"Bearer {installation_token}",
                "Accept": "application/vnd.github.diff"
            },
        ).text

        if diff is None:
            print(f"Diff is empty -> {diff}")


        diff = format_diff(diff)

        pr_files = get_pr_files(repo_owner=repo_owner, repo_name=repo_name, number=pr_number, installation_token=installation_token)


#         context = f"""
# Here's the diff:
# {diff}

# Here's context on the files affected:
# {pr_files}

"""

        if action in ("reopened", "opened", "synchronize"):
            review = await call_agent(diff)

            if review:
                submit_review(
                    data=json.loads(review),
                    owner=repo_owner,
                    repo=repo_name,
                    pull_number=pr_number,
                    installation_token=installation_token
                )
            else:
                print(f"No review was created -> {review}")
