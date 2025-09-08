# macrozero backend

FastAPI backend for GitHub workflow automation.

## Requirements

- Python 3.13+
- uv (Python package manager)

## Quick start

```bash
# from repo root
cd backend
uv sync
uv run uvicorn backend.server:app --reload --host 0.0.0.0 --port 8000
```

The server exposes a webhook endpoint at `POST /webhook` for GitHub events.

## Environment variables

Copy `.env.example` to `.env` and fill in values:

- DB_HOST, DB_PORT, DB_USERNAME, DB_PASSWORD, DB_DATABASE
- APP_ID (GitHub App ID)
- INSTALLATION_ID (GitHub App Installation ID)
- WEBHOOK_SECRET (GitHub App webhook secret)
- PRIVATE_KEY_PATH (path to the GitHub App private key PEM)

Optional:
- GITHUB_TOKEN (for local scripts if needed)

## GitHub App setup (summary)

1) Create a GitHub App, enable Pull request events, set the Webhook URL to `https://<your-domain>/webhook` and configure the same `WEBHOOK_SECRET`.
2) Install the App to your repository and note the Installation ID.
3) Download the private key and set `PRIVATE_KEY_PATH` to its location.

## Notes

- Run `uv run uvicorn backend.server:app` from the `backend` folder so imports resolve as `backend.*`.
- The server currently responds with a comment on PR events (`opened`, `reopened`, `synchronize`).