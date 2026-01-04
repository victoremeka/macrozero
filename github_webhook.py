import hmac
import hashlib
from typing import Any
from fastapi import HTTPException, Request
from integrations.github_client import GITHUB_WEBHOOK_SECRET
from pr_handler import handle_pull_request


APP_NAME = "macrozero"

def verify_signature(raw: bytes, sig_header: str | None):
    if not sig_header:
        raise HTTPException(403, "Missing X-Hub-Signature-256")
    if not GITHUB_WEBHOOK_SECRET:
        raise HTTPException(500, "Webhook secret not configured")
    expected = "sha256=" + hmac.new(GITHUB_WEBHOOK_SECRET.encode(), raw, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, sig_header):
        raise HTTPException(403, "Bad signature")


async def handle_webhook_payload(request: Request):
    raw = await request.body()

    try:
        verify_signature(raw, request.headers.get("X-Hub-Signature-256"))
    except HTTPException as e:
        raise e

    event = request.headers.get("X-GitHub-Event")
    payload : dict[str, Any] = await request.json()

    print("event ->", event, " action ->", payload.get("action"))

    if event == "pull_request":
        handle_pull_request(payload)