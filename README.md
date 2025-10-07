# Macrozero
_`A fork from my submission for a hackathon`_

AI code review co‑pilot for GitHub pull requests.

- Watches PR webhooks as a GitHub App
- Runs a two‑stage AI reviewer (analyze → package)
- Posts structured reviews with line‑anchored comments

## Quick start

### Prerequisites
- Docker and Docker Compose
- A MySQL/TiDB database (local or cloud)
- A GitHub App (App ID, Installation ID, Webhook Secret, Private Key)
- An LLM API key (Moonshot Kimi via LiteLLM)

### Local (Docker Compose)
1. Copy env example and fill in values:
	- `cp backend/.env.example backend/.env`
2. Ensure your GitHub App private key PEM exists. By default `docker-compose.yml`
	 mounts `./backend/certs/macrozero-app.2025-09-07.private-key.pem`; adjust the
	 secret path if you store the key elsewhere.
3. Run:
	- `docker compose up --build`
4. Open:
	- Backend: http://localhost:8000
	- Health: http://localhost:8000/healthz

### Local (direct)
Requires Python 3.13+ and [uv](https://docs.astral.sh/uv/):
- `cd backend`
- `uv sync`
- `uv run uvicorn server:app --host 0.0.0.0 --port 8000`

## Backend
- Framework: FastAPI + SQLModel (TiDB/MySQL)
- Agents: Google ADK SequentialAgent (reviewer → packager)
- LLM: LiteLLM with Moonshot Kimi
- GitHub App: Installation token auth; Create Review API
- Resilience: strict tool‑call prompts + server‑side fallback
- Health: `/healthz`

### Environment variables (backend)
Required:
- `DB_HOST`, `DB_PORT`, `DB_USERNAME`, `DB_PASSWORD`, `DB_DATABASE`
- `GITHUB_APP_ID`, `GITHUB_INSTALLATION_ID`, `GITHUB_WEBHOOK_SECRET`
- `GITHUB_PRIVATE_KEY_PATH` (file path inside container/VM)
- `KIMI_API_KEY`
Optional:
- `KIMI_API_BASE_URL`, `INIT_DB_ON_STARTUP` (default true)
- `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET` (optional OAuth login)
- `JWT_SECRET_KEY` (required if auth cookies are in use)

### Webhooks
Set your GitHub App webhook URL to:
- `POST /webhook`
- Signature verified via `GITHUB_WEBHOOK_SECRET`

### Review flow
1. Webhook hits FastAPI → orchestrator agent
2. Reviewer step produces structured analysis (JSON)
3. Packager step calls `create_pr_review` with line + side comments
4. Fallback: if model prints JSON instead of tool call, server posts it

## Frontend
The initial Vite/React UI has been removed while the backend hardens. A rebuilt
interface will land here later; until then the `frontend/` folder only contains a
placeholder README.

## Deployment
- Container: `backend/Dockerfile` (binds to `${PORT:-8000}`)
- Cloud Run: set envs; mount GitHub key via Secret Manager; consider `INIT_DB_ON_STARTUP=false` on first deploy

## Troubleshooting
- 422 on review post → ensure comments use `line` + `side` (not `position`)
- Model didn’t call tool → server fallback posts review if JSON is returned
- Cloud Run timeout → confirm `${PORT}` binding and `/healthz` works; disable DB init on startup

## Roadmap
- Diff→HEAD line mapping for precise inline anchors
- Review idempotency to prevent duplicates
- Structured logging and telemetry
- Issue triage agent + auto‑labels
- Replay harness for safe end‑to‑end tests
