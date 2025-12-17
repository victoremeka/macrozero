import os
import time
import requests
import jwt
import dotenv

dotenv.load_dotenv()

APP_ID = os.getenv("GITHUB_APP_ID")
GITHUB_WEBHOOK_SECRET= os.getenv("GITHUB_WEBHOOK_SECRET")
GITHUB_PRIVATE_KEY= os.getenv("GITHUB_PRIVATE_KEY")

def _private_key() -> str:
    if not GITHUB_PRIVATE_KEY:
        raise RuntimeError("GITHUB_PRIVATE_KEY not set")
    return GITHUB_PRIVATE_KEY

def _issue_jwt() -> str:
    now = int(time.time())
    payload = {"iat": now - 30, "exp": now + 540, "iss": APP_ID}
    return jwt.encode(payload, _private_key(), algorithm="RS256")

def _get_installation_id(owner:str, repo:str) -> str:
    res = requests.get(
        url=f"https://api.github.com/repos/{owner}/{repo}/installation",
        headers={
            "Authorization" : f"Bearer {_issue_jwt()}",
            "Accept": "application/vnd.github+json"
        }
    ).json()
    return res.get("id")

def _installation_token(owner: str, repo: str):
    token = requests.post(
        url=f"https://api.github.com/app/installations/{_get_installation_id(owner, repo)}/access_tokens",
        headers={
            "Authorization" : f"Bearer {_issue_jwt()}",
        },
    ).json()
    return token.get("token")
