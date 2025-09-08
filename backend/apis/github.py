from fastapi import Request
import hmac, hashlib, time, requests, os
import jwt
import dotenv

dotenv.load_dotenv()

APP_ID = os.getenv("APP_ID")
INSTALLATION_ID = os.getenv("INSTALLATION_ID")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
PRIVATE_KEY = open(os.getenv("PRIVATE_KEY_PATH")).read()

def get_installation_token():
    now = int(time.time())
    payload = {"iat": now, "exp": now + 600, "iss": APP_ID}
    jwt_token = jwt.encode(payload, PRIVATE_KEY, algorithm="RS256")
    headers = {"Authorization": f"Bearer {jwt_token}", "Accept": "application/vnd.github+json"}
    url = f"https://api.github.com/app/installations/{INSTALLATION_ID}/access_tokens"
    return requests.post(url, headers=headers).json()["token"]

async def handle_webhook_pull_request(request: Request):
    body = await request.body()
    sig = "sha256=" + hmac.new(WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(request.headers["X-Hub-Signature-256"], sig):
        return {"error": "invalid signature"}

    event = request.headers["X-GitHub-Event"]
    payload = await request.json()

    if event == "pull_request" and payload.get("action") in {"opened", "reopened"}:
        token = get_installation_token()
        headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}
        comment_url = payload["pull_request"]["comments_url"]
        requests.post(comment_url, headers=headers, json={"body": "👋 Agent saw this PR!"})