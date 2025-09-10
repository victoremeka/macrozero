import hmac, hashlib
from fastapi import HTTPException, Request
from integrations.github_client import (comment_on_pr, WEBHOOK_SECRET)
from services.github_sync import *

def verify_signature(raw: bytes, sig_header: str | None):
    """
    Verify that a webhook payload was sent by GitHub using HMAC signature validation.

    GitHub signs webhook payloads using the webhook secret configured in the app.
    This function validates the signature to ensure the request is authentic and
    hasn't been tampered with.

    Args:
        raw: The raw request body bytes (before any JSON parsing)
        sig_header: The X-Hub-Signature-256 header value from the request

    Raises:
        HTTPException: 
        - 403 if signature header is missing or invalid
        - 500 if webhook secret is not configured

    Security:
        - Uses constant-time comparison to prevent timing attacks
        - Requires the webhook secret to be configured in environment
        - Must be called with the raw request body, not parsed JSON

    Usage:
        raw_body = await request.body()
        verify_signature(raw_body, request.headers.get("X-Hub-Signature-256"))
    """
    if not sig_header:
        raise HTTPException(403, "Missing X-Hub-Signature-256")
    if not WEBHOOK_SECRET:
        raise HTTPException(500, "Webhook secret not configured")
    expected = "sha256=" + hmac.new(WEBHOOK_SECRET.encode(), raw, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, sig_header):
        raise HTTPException(403, "Bad signature")


async def handle_webhook_payload(request: Request):
    raw = await request.body()
    try:
        verify_signature(raw, request.headers.get("X-Hub-Signature-256"))
    except HTTPException as e:
        raise
    event = request.headers.get("X-GitHub-Event")
    payload : dict = await request.json()

    if event == "pull_request":
        handle_pull_request(payload=payload)
    elif event == "issues":
        handle_issue(payload=payload)
    else:
        return {"ignored": event}
    