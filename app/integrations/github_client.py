import os, time, requests, jwt
from typing import Any, Dict, Iterable, Optional
import dotenv
from contextvars import ContextVar
from contextlib import contextmanager

dotenv.load_dotenv()

# ENV (keep names you already use)
APP_ID = os.getenv("GITHUB_APP_ID")
INSTALLATION_ID = os.getenv("GITHUB_INSTALLATION_ID")
WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")
PRIVATE_KEY_PATH = os.getenv("GITHUB_PRIVATE_KEY_PATH")

API_BASE = "https://api.github.com"
# cache tokens per installation id instead of a single global token
_token_cache: Dict[str, Dict[str, Any]] = {}  # {inst_id: {"token": str, "exp": float}}

__all__ = [
    "APP_ID",
    "INSTALLATION_ID",
    "WEBHOOK_SECRET",
    "PRIVATE_KEY_PATH",
    "use_installation",
    "gh_request",
    "gh_json",
    "paginate",
    "get_pull_request_diff",
    "list_pr_commits",
]

# track the current installation id (per request/task); default to env INSTALLATION_ID
_CURRENT_INSTALLATION_ID: ContextVar[Optional[str]] = ContextVar(
    "current_installation_id", default=INSTALLATION_ID
)

def set_installation_id(installation_id: int | str) -> None:
    _CURRENT_INSTALLATION_ID.set(str(installation_id))

@contextmanager
def use_installation(installation_id: int | str):
    token = _CURRENT_INSTALLATION_ID.set(str(installation_id))
    try:
        yield
    finally:
        _CURRENT_INSTALLATION_ID.reset(token)

def _current_installation_id() -> str:
    inst = _CURRENT_INSTALLATION_ID.get() or INSTALLATION_ID
    if not inst:
        raise RuntimeError("No installation id configured")
    return str(inst)

def _private_key() -> str:
    """
    Load the GitHub App's private key from the configured file path.

    This function handles both absolute and relative paths:
    - Absolute paths are used as-is
    - Relative paths are resolved relative to the repository root
    - Falls back to checking relative to the backend/ directory

    Returns:
        str: The complete private key content as a string, including headers/footers.

    Raises:
        RuntimeError: If GITHUB_PRIVATE_KEY_PATH environment variable is not set,
                     or if the private key file cannot be found at the specified path.

    Security:
        The private key is read from disk on each call - no caching for security.
        Ensure the private key file has appropriate filesystem permissions (600).
    """
    if not PRIVATE_KEY_PATH:
        raise RuntimeError("GITHUB_PRIVATE_KEY_PATH not set")
    path = PRIVATE_KEY_PATH
    if not os.path.isabs(path):
        # resolve relative to repo root
        path = os.path.abspath(path)
        if not os.path.exists(path):
            # fallback relative to backend/
            here = os.path.dirname(__file__)
            cand = os.path.join(here, "..", path)
            if os.path.exists(cand):
                path = cand
    if not os.path.exists(path):
        raise RuntimeError(f"Private key not found: {path}")
    with open(path, "r") as f:
        return f.read()

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

def _installation_token() -> str:
    now = time.time()
    inst_id = _current_installation_id()
    cached = _token_cache.get(inst_id)
    if cached and now < cached["exp"] - 30:
        return cached["token"]

    headers = {"Authorization": f"Bearer {_issue_jwt()}", "Accept": "application/vnd.github+json"}
    url = f"{API_BASE}/app/installations/{inst_id}/access_tokens"
    r = requests.post(url, headers=headers, timeout=15)
    if r.status_code >= 300:
        raise RuntimeError(f"Token error {r.status_code}: {r.text}")
    data = r.json()

    expires_at = data.get("expires_at")
    exp_epoch = now + 3000
    if expires_at:
        from datetime import datetime, timezone
        exp_epoch = datetime.strptime(expires_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()

    _token_cache[inst_id] = {"token": data["token"], "exp": exp_epoch}
    return data["token"]

def _headers(extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """
    Generate standard headers for GitHub API requests with authentication.

    Creates a base set of headers including:
    - Authorization with installation token
    - Accept header for GitHub's API version
    - API version specification

    Args:
        extra: Optional dictionary of additional headers to merge with base headers.
               Extra headers will override base headers if keys conflict.

    Returns:
        Dict[str, str]: Complete headers dictionary ready for API requests.

    Usage:
        Used internally by gh_request(). Most callers should use gh_request() or
        gh_json() instead of calling this directly.
    """
    base = {
        "Authorization": f"token {_installation_token()}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if extra:
        base.update(extra)
    return base

def gh_request(method: str, path: str, *, params=None, json=None, headers=None, timeout=30):
    """
    Make an authenticated HTTP request to the GitHub API.

    This is the low-level function for all GitHub API interactions. It handles:
    - Authentication via installation tokens
    - Standard GitHub API headers
    - Error handling for non-2xx responses
    - Both absolute URLs and relative API paths

    Args:
        method: HTTP method (GET, POST, PUT, PATCH, DELETE, etc.)
        path: API endpoint path (e.g., "/repos/owner/repo") or full URL
        params: Optional query parameters as dict
        json: Optional JSON request body as dict
        headers: Optional additional headers to merge with defaults
        timeout: Request timeout in seconds (default: 30)

    Returns:
        requests.Response: The response object for further processing

    Raises:
        RuntimeError: If the request fails (status code >= 300) with details

    Usage:
        For JSON responses, prefer gh_json(). For raw responses or when you need
        the full response object, use this function directly.
    """
    url = path if path.startswith("http") else f"{API_BASE}{path}"
    r = requests.request(method.upper(), url, params=params, json=json, headers=_headers(headers), timeout=timeout)
    if r.status_code >= 300:
        raise RuntimeError(f"GitHub API {r.status_code}: {r.text}")
    return r

def gh_json(method: str, path: str, **kw):
    """
    Make an authenticated GitHub API request and parse the JSON response.

    This is the preferred function for most GitHub API interactions that return JSON.
    It handles the common case of making a request and parsing the response automatically.

    Args:
        method: HTTP method (GET, POST, PUT, PATCH, DELETE, etc.)
        path: API endpoint path (e.g., "/repos/owner/repo") or full URL
        **kw: Additional keyword arguments passed to gh_request()
              (params, json, headers, timeout)

    Returns:
        Union[dict, list, str, None]: 
        - dict/list for JSON responses
        - None for 204 No Content responses
        - str for non-JSON responses

    Raises:
        RuntimeError: If the underlying HTTP request fails
        json.JSONDecodeError: If response claims to be JSON but isn't parseable

    Usage:
        This is the most commonly used function for GitHub API calls.
        Use gh_request() if you need the raw response object.
    """
    r = gh_request(method, path, **kw)
    if r.status_code == 204:
        return None
    ct = r.headers.get("Content-Type", "")
    if "json" in ct:
        return r.json()
    return r.text

def paginate(path: str, params: Optional[Dict[str, Any]] = None, per_page: int = 100) -> Iterable[dict]:
    """
    Paginate through a GitHub API endpoint that returns a list of items.

    GitHub API endpoints that return collections are paginated. This function
    automatically handles pagination, yielding individual items from all pages.

    Args:
        path: API endpoint path (e.g., "/repos/owner/repo/issues")
        params: Optional query parameters to include with each request
        per_page: Number of items to request per page (max 100 for most endpoints)

    Yields:
        dict: Individual items from the paginated response

    Returns:
        Iterator[dict]: Generator yielding each item across all pages

    Raises:
        RuntimeError: If any page request fails

    Usage:
        for issue in paginate("/repos/owner/repo/issues"):
            print(issue["title"])
        
        # Convert to list if needed
        all_issues = list(paginate("/repos/owner/repo/issues"))
    """
    page = 1
    while True:
        p = dict(params or {})
        p.update({"per_page": per_page, "page": page})
        data = gh_json("GET", path, params=p)
        if not isinstance(data, list) or not data:
            break
        for item in data:
            yield item
        if len(data) < per_page:
            break
        page += 1

def get_pull_request_diff(owner: str, repo: str, number: int):
    diff = gh_request(method="GET", path=f"/repos/{owner}/{repo}/pulls/{number}", headers={"Accept": "application/vnd.github.v3.diff",}).text
    return diff

def list_pr_commits(owner: str, repo_name: str, number: int) -> list[dict]:
    """Return all commits for a pull request."""
    return list(paginate(f"/repos/{owner}/{repo_name}/pulls/{number}/commits"))
