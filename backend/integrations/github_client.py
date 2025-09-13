import os, time, requests, jwt
from typing import Any, Dict, Iterable, List, Optional
import dotenv

dotenv.load_dotenv()

# ENV (keep names you already use)
APP_ID = os.getenv("GITHUB_APP_ID")
INSTALLATION_ID = os.getenv("GITHUB_INSTALLATION_ID")
WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")
PRIVATE_KEY_PATH = os.getenv("GITHUB_PRIVATE_KEY_PATH")

API_BASE = "https://api.github.com"
_token_cache: Dict[str, Any] = {"token": None, "exp": 0}

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
    payload = {"iat": now - 30, "exp": now + 600, "iss": APP_ID}
    return jwt.encode(payload, _private_key(), algorithm="RS256")

def _installation_token() -> str:
    """
    Obtain an installation access token for authenticating GitHub API requests.

    This function implements token caching with automatic refresh:
    - Returns cached token if still valid (with 30-second buffer)
    - Otherwise, exchanges a JWT for a new installation token
    - Caches the new token with its expiration time

    The installation token allows the app to act on behalf of the installation,
    accessing repositories and performing actions as the GitHub App.

    Returns:
        str: A valid GitHub installation access token for API authentication.

    Raises:
        RuntimeError: If the token request fails (network, auth, or API errors).
        
    Side Effects:
        Updates the global _token_cache with the new token and expiration.

    Usage:
        This is an internal function - use _headers() or gh_request() for API calls.
    """
    now = time.time()
    if _token_cache["token"] and now < _token_cache["exp"] - 30:
        return _token_cache["token"]
    headers = {"Authorization": f"Bearer {_issue_jwt()}", "Accept": "application/vnd.github+json"}
    url = f"{API_BASE}/app/installations/{INSTALLATION_ID}/access_tokens"
    r = requests.post(url, headers=headers, timeout=15)
    if r.status_code >= 300:
        raise RuntimeError(f"Token error {r.status_code}: {r.text}")
    data = r.json()
    expires_at = data.get("expires_at")  # e.g. 2024-01-01T00:00:00Z
    exp_epoch = now + 3000
    if expires_at:
        # crude parse
        try:
            from datetime import datetime, timezone
            exp_epoch = datetime.strptime(expires_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()
        except:
            pass
    _token_cache.update({"token": data["token"], "exp": exp_epoch})
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

# High-level helpers
def get_repo(owner: str, repo: str): 
    """
    Get detailed information about a GitHub repository.

    Args:
        owner: Repository owner (username or organization name)
        repo: Repository name

    Returns:
        dict: Repository metadata including name, description, permissions, etc.

    Raises:
        RuntimeError: If repository doesn't exist or access is denied

    Usage:
        repo_info = get_repo("octocat", "Hello-World")
        print(repo_info["description"])
    """
    return gh_json("GET", f"/repos/{owner}/{repo}")

def list_pull_requests(owner: str, repo: str, state="open") -> List[dict]:
    """
    List pull requests in a repository, optionally filtered by state.

    Args:
        owner: Repository owner (username or organization name)
        repo: Repository name  
        state: Filter by state - "open", "closed", or "all" (default: "open")

    Returns:
        List[dict]: List of pull request objects with metadata, links, etc.

    Usage:
        open_prs = list_pull_requests("owner", "repo")
        all_prs = list_pull_requests("owner", "repo", state="all")
    """
    return list(paginate(f"/repos/{owner}/{repo}/pulls", {"state": state}))

def get_pull_request_diff(owner: str, repo: str, number: int):
    return gh_request(method="get", path=f"/repos/{owner}/{repo}/pulls/{number}", headers={"Accept": "application/vnd.github.v3.diff",})

def get_pull_request(owner: str, repo: str, number: int):
    """
    Get detailed information about a specific pull request.

    Args:
        owner: Repository owner (username or organization name)
        repo: Repository name
        number: Pull request number (not the same as issue number)

    Returns:
        dict: Pull request object with detailed metadata, including:
        - title, body, state, mergeable status
        - head/base branch information
        - author, reviewers, assignees
        - comments_url, commits_url, etc.

    Raises:
        RuntimeError: If PR doesn't exist or access is denied

    Usage:
        pr = get_pull_request("owner", "repo", 123)
        print(f"PR: {pr['title']} by {pr['user']['login']}")
    """
    return gh_json("GET", f"/repos/{owner}/{repo}/pulls/{number}")

def list_pr_commits(owner: str, repo_name: str, number: int):
    """
    List all commits in a pull request.

    Args:
        owner: Repository owner (username or organization name)
        repo_name: Repository name
        number: Pull request number

    Returns:
        List[dict]: List of commit objects with SHA, message, author, etc.

    Usage:
        commits = list_pr_commits("owner", "repo", 123)
        for commit in commits:
            print(f"{commit['sha'][:7]}: {commit['commit']['message']}")
    """
    return list(paginate(f"/repos/{owner}/{repo_name}/pulls/{number}/commits"))

def list_pr_files(owner: str, repo: str, number: int):
    """
    List all files changed in a pull request.

    Args:
        owner: Repository owner (username or organization name) 
        repo: Repository name
        number: Pull request number

    Returns:
        List[dict]: List of file objects with filename, status, changes, etc.
        Each file object includes:
        - filename: Path to the file
        - status: "added", "modified", "removed", "renamed"
        - additions/deletions: Line change counts
        - patch: The actual diff content (if available)

    Usage:
        files = list_pr_files("owner", "repo", 123)
        for file in files:
            print(f"{file['status']}: {file['filename']} (+{file['additions']}/-{file['deletions']})")
    """
    return list(paginate(f"/repos/{owner}/{repo}/pulls/{number}/files"))

def comment_on_pr(owner: str, repo: str, number: int, body: str, commit_sha: str, path: str):
    """
    Add a comment to a pull request.

    Args:
        owner: Repository owner (username or organization name)
        repo: Repository name  
        number: Pull request number
        body: Comment text (supports Markdown formatting)

    Returns:
        dict: Created comment object with id, url, created_at, etc.

    Raises:
        RuntimeError: If PR doesn't exist, is locked, or access is denied

    Usage:
        comment = comment_on_pr("owner", "repo", 123, "LGTM! 🚀")
        print(f"Comment created: {comment['html_url']}")
    """
    pr = get_pull_request(owner, repo, number)
    return gh_json("POST", pr["comments_url"], json={"body": body, "commmit_id": commit_sha, "path": path})

def merge_pr(owner: str, repo: str, number: int, method="squash", title: str | None = None):
    """
    Merge a pull request using the specified merge method.

    Args:
        owner: Repository owner (username or organization name)
        repo: Repository name
        number: Pull request number
        method: Merge method - "merge", "squash", or "rebase" (default: "squash")
        title: Optional custom commit title for squash/merge commits

    Returns:
        dict: Merge result with SHA, merged status, and message

    Raises:
        RuntimeError: If PR can't be merged (conflicts, checks failing, etc.)

    Usage:
        result = merge_pr("owner", "repo", 123, method="squash", title="feat: add new feature")
        print(f"Merged as {result['sha']}")
    """
    payload = {"merge_method": method}
    if title: payload["commit_title"] = title
    return gh_json("PUT", f"/repos/{owner}/{repo}/pulls/{number}/merge", json=payload)

def list_issues(owner: str, repo: str, state="open"):
    """
    List issues in a repository, excluding pull requests.

    Args:
        owner: Repository owner (username or organization name)
        repo: Repository name
        state: Filter by state - "open", "closed", or "all" (default: "open")

    Returns:
        List[dict]: List of issue objects (PRs are filtered out)

    Note:
        GitHub's issues API includes pull requests, but this function filters
        them out to return only actual issues.

    Usage:
        issues = list_issues("owner", "repo")
        open_issues = list_issues("owner", "repo", state="open")
    """
    items = list(paginate(f"/repos/{owner}/{repo}/issues", {"state": state}))
    return [i for i in items if "pull_request" not in i]

def get_issue(owner: str, repo: str, number: int):
    """
    Get detailed information about a specific issue (not a pull request).

    Args:
        owner: Repository owner (username or organization name)
        repo: Repository name  
        number: Issue number

    Returns:
        dict: Issue object with title, body, labels, assignees, etc.

    Raises:
        ValueError: If the number refers to a pull request instead of an issue
        RuntimeError: If issue doesn't exist or access is denied

    Usage:
        issue = get_issue("owner", "repo", 456)
        print(f"Issue: {issue['title']} - {issue['state']}")
    """
    data = gh_json("GET", f"/repos/{owner}/{repo}/issues/{number}")
    if "pull_request" in data:
        raise ValueError("Requested number is a pull request")
    return data

def create_issue(owner: str, repo: str, title: str, body: str, labels: Optional[List[str]] = None):
    """
    Create a new issue in a repository.

    Args:
        owner: Repository owner (username or organization name)
        repo: Repository name
        title: Issue title (required)
        body: Issue description/body text (supports Markdown)
        labels: Optional list of label names to apply to the issue

    Returns:
        dict: Created issue object with number, url, created_at, etc.

    Raises:
        RuntimeError: If creation fails (permissions, invalid labels, etc.)

    Usage:
        issue = create_issue("owner", "repo", "Bug report", "Description here", ["bug", "urgent"])
        print(f"Created issue #{issue['number']}")
    """
    payload = {"title": title, "body": body}
    if labels: payload["labels"] = labels
    return gh_json("POST", f"/repos/{owner}/{repo}/issues", json=payload)

def add_labels(owner: str, repo: str, number: int, labels: List[str]):
    """
    Add labels to an existing issue or pull request.

    Args:
        owner: Repository owner (username or organization name)
        repo: Repository name
        number: Issue or pull request number
        labels: List of label names to add

    Returns:
        dict: Response with updated labels list

    Raises:
        RuntimeError: If labels don't exist in the repository or access is denied

    Usage:
        add_labels("owner", "repo", 123, ["bug", "priority-high"])
    """
    return gh_json("POST", f"/repos/{owner}/{repo}/issues/{number}/labels", json={"labels": labels})

def remove_label(owner: str, repo: str, number: int, label: str):
    """
    Remove a specific label from an issue or pull request.

    Args:
        owner: Repository owner (username or organization name)
        repo: Repository name
        number: Issue or pull request number
        label: Label name to remove

    Returns:
        bool: True if successful

    Raises:
        RuntimeError: If label doesn't exist on the issue or access is denied

    Usage:
        remove_label("owner", "repo", 123, "wontfix")
    """
    gh_request("DELETE", f"/repos/{owner}/{repo}/issues/{number}/labels/{label}")
    return True

def get_commit(owner: str, repo: str, sha: str):
    """
    Get detailed information about a specific commit.

    Args:
        owner: Repository owner (username or organization name)
        repo: Repository name
        sha: Commit SHA hash (full or abbreviated)

    Returns:
        dict: Commit object with message, author, files changed, stats, etc.

    Usage:
        commit = get_commit("owner", "repo", "abc123def456")
        print(f"Commit: {commit['commit']['message']}")
        print(f"Files changed: {len(commit['files'])}")
    """
    return gh_json("GET", f"/repos/{owner}/{repo}/commits/{sha}")

def get_diff(owner: str, repo: str, base: str, head: str) -> str:
    """
    Get the diff between two commits, branches, or tags as a unified diff string.

    Args:
        owner: Repository owner (username or organization name)
        repo: Repository name
        base: Base reference (commit SHA, branch, or tag name)
        head: Head reference (commit SHA, branch, or tag name)

    Returns:
        str: Unified diff format showing changes between base and head

    Usage:
        diff = get_diff("owner", "repo", "main", "feature-branch")
        diff = get_diff("owner", "repo", "abc123", "def456")
        print(diff)  # Shows file changes in patch format
    """
    r = gh_request("GET", f"/repos/{owner}/{repo}/compare/{base}...{head}",
                   headers={"Accept": "application/vnd.github.v3.diff"})
    return r.text

def create_check_run(owner: str, repo: str, name: str, head_sha: str, status="in_progress"):
    """
    Create a check run for a specific commit (used by GitHub Apps for CI/status checks).

    Args:
        owner: Repository owner (username or organization name)
        repo: Repository name
        name: Display name for the check run (e.g., "Build", "Tests", "Linting")
        head_sha: SHA of the commit to attach the check run to
        status: Initial status - "queued", "in_progress", or "completed"

    Returns:
        dict: Created check run object with id, status, url, etc.

    Usage:
        check = create_check_run("owner", "repo", "CI Build", "abc123def")
        # Later update with update_check_run(owner, repo, check["id"], "success")
    """
    return gh_json("POST", f"/repos/{owner}/{repo}/check-runs",
                   json={"name": name, "head_sha": head_sha, "status": status},
                   headers={"Accept": "application/vnd.github+json"})

def update_check_run(owner: str, repo: str, check_run_id: int, conclusion: str, summary: str = ""):
    """
    Update a check run with completion status and results.

    Args:
        owner: Repository owner (username or organization name)
        repo: Repository name
        check_run_id: ID of the check run to update (from create_check_run response)
        conclusion: Final result - "success", "failure", "neutral", "cancelled", 
                   "skipped", "timed_out", or "action_required"
        summary: Optional summary text describing the results

    Returns:
        dict: Updated check run object

    Usage:
        update_check_run("owner", "repo", 123456, "success", "All tests passed!")
        update_check_run("owner", "repo", 123456, "failure", "3 tests failed")
    """
    payload = {"conclusion": conclusion, "status": "completed", "output": {"title": "Result", "summary": summary}}
    return gh_json("PATCH", f"/repos/{owner}/{repo}/check-runs/{check_run_id}",
                   json=payload, headers={"Accept": "application/vnd.github+json"})
