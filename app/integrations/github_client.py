import os
import time
import requests
from requests.auth import HTTPBasicAuth
import jwt
from typing import Any, Dict, Iterable, Optional
import dotenv



dotenv.load_dotenv()

APP_ID = os.getenv("GITHUB_APP_ID")
WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")
GITHUB_PRIVATE_KEY= os.getenv("GITHUB_PRIVATE_KEY")
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIEND_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")

API_BASE = "https://api.github.com"

def _private_key() -> str:
    if not GITHUB_PRIVATE_KEY:
        raise RuntimeError("GITHUB_PRIVATE_KEY not set")
    return GITHUB_PRIVATE_KEY

def _issue_jwt() -> str:
    """
    Generate a short-lived JWT for authenticating as a GitHub App.

    The token:
    - Uses the GitHub App ID as the issuer (iss).
    - Sets 'iat' (issued-at) 30 seconds in the past to mitigate clock skew.
    - Expires 10 minutes after the current time (GitHub requires <= 10 minutes).
    - Is signed with the app's private key using RS256.

    Returns:
        str: The encoded JSON Web Token suitable for GitHub's /app and installation APIs.

    Raises:
        jwt.PyJWTError: If encoding fails.
        ValueError / OSError: If the private key cannot be loaded.

    Security:
        The private key must be securely stored and never logged. The returned JWT
        should not be cached beyond its expiration.
    """
    now = int(time.time())
    payload = {"iat": now - 30, "exp": now + 540, "iss": APP_ID}
    return jwt.encode(payload, _private_key(), algorithm="RS256")

def _get_installation_id(owner:str, repo:str) -> str:
    res = requests.get(
        url=f"{API_BASE}/repos/{owner}/{repo}/installation",
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

print(_installation_token(owner="victoremeka", repo="macrozero-test-repo"))