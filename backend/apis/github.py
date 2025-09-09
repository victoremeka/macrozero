from fastapi import HTTPException, Request
import hmac, hashlib, time, requests, os
import jwt
import dotenv

dotenv.load_dotenv()

APP_ID = os.getenv("APP_ID")
INSTALLATION_ID = os.getenv("INSTALLATION_ID")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
with open(os.getenv("PRIVATE_KEY_PATH")) as f:
    PRIVATE_KEY = f.read()

def get_installation_token():
    now = int(time.time())
    payload = {"iat": now, "exp": now + 600, "iss": APP_ID}
    jwt_token = jwt.encode(payload, PRIVATE_KEY, algorithm="RS256")
    headers = {"Authorization": f"Bearer {jwt_token}", "Accept": "application/vnd.github+json"}
    url = f"https://api.github.com/app/installations/{INSTALLATION_ID}/access_tokens"
    return requests.post(url, headers=headers).json()["token"]

def verify_signature(payload_body, secret_token, signature_header):
    """Verify that the payload was sent from GitHub by validating SHA256.

    Raise and return 403 if not authorized.

    Args:
        payload_body: original request body to verify (request.body())
        secret_token: GitHub app webhook token (WEBHOOK_SECRET)
        signature_header: header received from GitHub (x-hub-signature-256)
    """
    if not signature_header:
        raise HTTPException(status_code=403, detail="x-hub-signature-256 header is missing!")
    hash_object = hmac.new(secret_token.encode('utf-8'), msg=payload_body, digestmod=hashlib.sha256)
    expected_signature = "sha256=" + hash_object.hexdigest()
    if not hmac.compare_digest(expected_signature, signature_header):
        raise HTTPException(status_code=403, detail="Request signatures didn't match!")

async def handle_webhook_pull_request(request: Request):
    body = await request.body()
    verify_signature(body, secret_token=WEBHOOK_SECRET, signature_header=request.headers.get("X-Hub-Signature-256"))

    event = request.headers["X-GitHub-Event"]
    payload = await request.json()

    if event == "pull_request" and payload.get("action") in {"opened", "reopened"}:
        token = get_installation_token()
        headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}
        comment_url = payload["pull_request"]["comments_url"]
        requests.post(comment_url, headers=headers, json={"body": "👋 Agent saw this PR!"})

