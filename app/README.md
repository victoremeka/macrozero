# macrozero backend

FastAPI service that handles GitHub PR webhooks and triggers the AI reviewer.

## Setup

Prerequisites: Python 3.13+, [uv](https://docs.astral.sh/uv/).

```bash
cd backend
uv sync
uv run uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

The app serves `POST /webhook` for GitHub and `GET /healthz` for probes.

## Configuration

Copy `.env.example` → `.env` and provide:

**Required**
- `DB_HOST`, `DB_PORT`, `DB_USERNAME`, `DB_PASSWORD`, `DB_DATABASE`
- `GITHUB_APP_ID`, `GITHUB_INSTALLATION_ID`
- `GITHUB_PRIVATE_KEY_PATH` (GitHub App PEM file)
- `GITHUB_WEBHOOK_SECRET` (validates `X-Hub-Signature-256`)
- `KIMI_API_KEY`

**Optional**
- `KIMI_API_BASE_URL`, `INIT_DB_ON_STARTUP`
- `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`
- `JWT_SECRET_KEY`

## GitHub App checklist
1. Create an App, enable pull request + issue events, set webhook to `https://<your-domain>/webhook`.
2. Use the same secret value for the App and `GITHUB_WEBHOOK_SECRET`.
3. Install the App, capture the installation ID, and place the private key where `GITHUB_PRIVATE_KEY_PATH` points.

## Operational notes
- Run commands from `backend/` so imports resolve.
- Webhook processing currently handles PR, PR review, and issue events; review comments are ignored.
- All webhook requests must include `X-Hub-Signature-256` signed with `GITHUB_WEBHOOK_SECRET`.
