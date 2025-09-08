import requests
import os
import hmac
import hashlib
import time
import jwt
from typing import Dict, Any, List, Optional

from core.config import settings


def get_installation_token() -> str:
    """
    Get GitHub App installation token
    """
    if not settings.github.app_id or not settings.github.installation_id:
        raise ValueError("GitHub App ID and Installation ID must be configured")

    private_key = None
    if settings.github.private_key_path:
        with open(settings.github.private_key_path, "r") as f:
            private_key = f.read()

    if not private_key:
        raise ValueError("GitHub App private key not found")

    now = int(time.time())
    payload = {"iat": now, "exp": now + 600, "iss": settings.github.app_id}
    jwt_token = jwt.encode(payload, private_key, algorithm="RS256")

    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/vnd.github+json",
    }
    url = f"https://api.github.com/app/installations/{settings.github.installation_id}/access_tokens"

    response = requests.post(url, headers=headers)
    response.raise_for_status()
    return response.json()["token"]


def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """
    Verify GitHub webhook signature
    """
    if not settings.github.webhook_secret:
        return False

    expected = (
        "sha256="
        + hmac.new(
            settings.github.webhook_secret.encode(), payload, hashlib.sha256
        ).hexdigest()
    )

    return hmac.compare_digest(signature, expected)


def get_user_repos(username: str) -> Optional[List[Dict[str, Any]]]:
    """
    Get user repositories
    """
    if not settings.github.token:
        raise ValueError("GitHub token not configured")

    url = f"https://api.github.com/users/{username}/repos"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {settings.github.token}",
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return None


def create_repo(repo_name: str, description: str = "") -> Optional[Dict[str, Any]]:
    """
    Create a new repository
    """
    if not settings.github.token:
        raise ValueError("GitHub token not configured")

    url = "https://api.github.com/user/repos"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {settings.github.token}",
    }

    data = {"name": repo_name, "description": description, "private": False}

    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 201:
        return response.json()
    else:
        return None
