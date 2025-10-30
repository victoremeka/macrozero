# macrozero code review service

Built with Python.

## Setup

Prerequisites: Python 3.13+, [uv](https://docs.astral.sh/uv/).

```bash
cd app
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

## Operational notes
- Run commands from `app/` so imports resolve.
- Webhook processing currently handles PR, PR review, and issue events; review comments are ignored.
- All webhook requests must include `X-Hub-Signature-256` signed with `GITHUB_WEBHOOK_SECRET`.
