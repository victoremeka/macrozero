from fastapi import FastAPI, Request, Depends
from sqlmodel import Session
import requests

from core.config import settings
from core.database import get_session, create_db_and_tables
from services import github as github_service

app = FastAPI()


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


@app.post("/webhook")
async def webhook(request: Request, db: Session = Depends(get_session)):
    body = await request.body()
    sig = request.headers.get("X-Hub-Signature-256", "")

    if not github_service.verify_webhook_signature(body, sig):
        return {"error": "invalid signature"}

    event = request.headers.get("X-GitHub-Event", "")
    payload = await request.json()

    if event == "pull_request" and payload.get("action") in {"opened", "reopened"}:
        token = github_service.get_installation_token()
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
        }
        comment_url = payload["pull_request"]["comments_url"]
        requests.post(
            comment_url, headers=headers, json={"body": "👋 Agent saw this PR!"}
        )
