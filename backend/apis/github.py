import os, time, hmac, hashlib, requests, jwt, json
from typing import Any, Dict, Iterable, List, Optional
from fastapi import HTTPException, Request
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
    now = int(time.time())
    payload = {"iat": now - 30, "exp": now + 600, "iss": APP_ID}
    return jwt.encode(payload, _private_key(), algorithm="RS256")

def _installation_token() -> str:
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
    base = {
        "Authorization": f"token {_installation_token()}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if extra:
        base.update(extra)
    return base

def gh_request(method: str, path: str, *, params=None, json=None, headers=None, timeout=30):
    url = path if path.startswith("http") else f"{API_BASE}{path}"
    r = requests.request(method.upper(), url, params=params, json=json, headers=_headers(headers), timeout=timeout)
    if r.status_code >= 300:
        raise RuntimeError(f"GitHub API {r.status_code}: {r.text}")
    return r

def gh_json(method: str, path: str, **kw):
    r = gh_request(method, path, **kw)
    if r.status_code == 204:
        return None
    ct = r.headers.get("Content-Type", "")
    if "json" in ct:
        return r.json()
    return r.text

def paginate(path: str, params: Optional[Dict[str, Any]] = None, per_page: int = 100) -> Iterable[dict]:
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

# Webhook verification
def verify_signature(raw: bytes, sig_header: str | None):
    if not sig_header:
        raise HTTPException(403, "Missing X-Hub-Signature-256")
    if not WEBHOOK_SECRET:
        raise HTTPException(500, "Webhook secret not configured")
    expected = "sha256=" + hmac.new(WEBHOOK_SECRET.encode(), raw, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, sig_header):
        raise HTTPException(403, "Bad signature")

# High-level helpers
def get_repo(owner: str, repo: str): return gh_json("GET", f"/repos/{owner}/{repo}")

def list_pull_requests(owner: str, repo: str, state="open") -> List[dict]:
    return list(paginate(f"/repos/{owner}/{repo}/pulls", {"state": state}))

def get_pull_request(owner: str, repo: str, number: int):
    return gh_json("GET", f"/repos/{owner}/{repo}/pulls/{number}")

def list_pr_commits(owner: str, repo: str, number: int):
    return list(paginate(f"/repos/{owner}/{repo}/pulls/{number}/commits"))

def list_pr_files(owner: str, repo: str, number: int):
    return list(paginate(f"/repos/{owner}/{repo}/pulls/{number}/files"))

def comment_on_pr(owner: str, repo: str, number: int, body: str):
    pr = get_pull_request(owner, repo, number)
    return gh_json("POST", pr["comments_url"], json={"body": body})

def merge_pr(owner: str, repo: str, number: int, method="squash", title: str | None = None):
    payload = {"merge_method": method}
    if title: payload["commit_title"] = title
    return gh_json("PUT", f"/repos/{owner}/{repo}/pulls/{number}/merge", json=payload)

def list_issues(owner: str, repo: str, state="open"):
    items = list(paginate(f"/repos/{owner}/{repo}/issues", {"state": state}))
    return [i for i in items if "pull_request" not in i]

def get_issue(owner: str, repo: str, number: int):
    data = gh_json("GET", f"/repos/{owner}/{repo}/issues/{number}")
    if "pull_request" in data:
        raise ValueError("Requested number is a pull request")
    return data

def create_issue(owner: str, repo: str, title: str, body: str, labels: Optional[List[str]] = None):
    payload = {"title": title, "body": body}
    if labels: payload["labels"] = labels
    return gh_json("POST", f"/repos/{owner}/{repo}/issues", json=payload)

def add_labels(owner: str, repo: str, number: int, labels: List[str]):
    return gh_json("POST", f"/repos/{owner}/{repo}/issues/{number}/labels", json={"labels": labels})

def remove_label(owner: str, repo: str, number: int, label: str):
    gh_request("DELETE", f"/repos/{owner}/{repo}/issues/{number}/labels/{label}")
    return True

def get_commit(owner: str, repo: str, sha: str):
    return gh_json("GET", f"/repos/{owner}/{repo}/commits/{sha}")

def get_diff(owner: str, repo: str, base: str, head: str) -> str:
    r = gh_request("GET", f"/repos/{owner}/{repo}/compare/{base}...{head}",
                   headers={"Accept": "application/vnd.github.v3.diff"})
    return r.text

def create_check_run(owner: str, repo: str, name: str, head_sha: str, status="in_progress"):
    return gh_json("POST", f"/repos/{owner}/{repo}/check-runs",
                   json={"name": name, "head_sha": head_sha, "status": status},
                   headers={"Accept": "application/vnd.github+json"})

def update_check_run(owner: str, repo: str, check_run_id: int, conclusion: str, summary: str = ""):
    payload = {"conclusion": conclusion, "status": "completed", "output": {"title": "Result", "summary": summary}}
    return gh_json("PATCH", f"/repos/{owner}/{repo}/check-runs/{check_run_id}",
                   json=payload, headers={"Accept": "application/vnd.github+json"})

# Webhook handler
async def handle_webhook_pull_request(request: Request):
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