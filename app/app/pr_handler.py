import json
import os
from typing import Any
from google import genai
from google.genai import types
import requests
from integrations.github_client import _installation_token

from .agent import call_agent


APP_TAG = r"@macrozeroai" # for v2 (mentions)

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY"),
)

def dump_to_json(payload, name, is_json=True):
    if is_json:
        with open(f"payloads/{name}.json", "w") as file:
            json.dump(payload, fp=file, indent=2)
    else:
        with open(f"{name}.txt", "w") as f:
            f.write(payload)

def embed(str:str):
    embeddings = client.models.embed_content(
        model="gemini-embedding-001",
        contents=str,
        config=types.EmbedContentConfig(output_dimensionality=768),
    ).embeddings

    if embeddings:
        return embeddings[0].values

async def handle_pull_request(payload: dict[str, Any]):
    # find @ tag -> ^(@@).+(@@)$
    # diff start -> ^(diff)
    dump_to_json(payload, "pr")

    pr = payload.get("pull_request")

    if pr:
        action = payload["action"]
        body = pr["title"] + "\n\n" + pr["body"]
        pr_number = pr["number"]
        pr_url = pr["url"]

        diff = requests.get(
            pr_url,
            headers={
                "Authorization": f"Bearer {_installation_token()}",
                "Accept": "application/vnd.github.diff"
            },
        )
        dump_to_json(diff, "diff", is_json=False)

        commits = requests.get(
            pr["commits_url"],
            headers={
                "Authorization": f"Bearer {_installation_token()}",
            },
        )
        dump_to_json(commits.json(), "commits")


        if action == "reopened" or "opened" or "synchronize":
            call_agent(diff)


    pass
    # route to agent
