import hmac, hashlib
from fastapi import HTTPException, Request

from integrations.github_client import *

# Webhook verification
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


# Webhook handler
async def handle_webhook_pull_request(request: Request):
    """
    Handle incoming GitHub webhook events for pull requests.

    This function processes webhook payloads from GitHub, validates their authenticity,
    and performs automated actions based on pull request events.

    Args:
        request: FastAPI Request object containing the webhook payload

    Returns:
        dict: Response indicating the processing status and action taken

    Security:
        - Verifies webhook signature using HMAC-SHA256
        - Only processes events from authenticated GitHub sources

    Events Handled:
        - "opened": New pull request created
        - "reopened": Previously closed PR was reopened  
        - "synchronize": New commits pushed to existing PR

    Actions Performed:
        - Posts an acknowledgment comment on qualifying PRs
        - Can be extended to trigger CI, code analysis, etc.

    Usage:
        # In FastAPI app:
        @app.post("/webhook/github")
        async def webhook_endpoint(request: Request):
            return await handle_webhook_pull_request(request)

    Error Handling:
        - Returns error details if signature validation fails
        - Gracefully handles API failures with error messages
    """
    raw = await request.body()
    try:
        verify_signature(raw, request.headers.get("X-Hub-Signature-256"))
    except HTTPException as e:
        raise
    event = request.headers.get("X-GitHub-Event")
    if event != "pull_request":
        return {"ignored": event}
    payload = await request.json()
    action = payload.get("action")
    if action in {"opened", "reopened", "synchronize"}:
        pr = payload["pull_request"]
        owner = pr["base"]["repo"]["owner"]["login"]
        repo = pr["base"]["repo"]["name"]
        number = pr["number"]
        try:
            comment_on_pr(owner, repo, number, "👋 Automation acknowledged this pull request.")
        except Exception as e:
            return {"status": "error", "detail": str(e)}
    return {"status": "ok", "action": action}