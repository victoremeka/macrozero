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
uv run uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

The server exposes a webhook endpoint at `POST /webhook` for GitHub events.

## Environment variables

Copy `.env.example` to `.env` and fill in values:

- DB_HOST, DB_PORT, DB_USERNAME, DB_PASSWORD, DB_DATABASE
- GITHUB_APP_ID (GitHub App ID)
- GITHUB_INSTALLATION_ID (GitHub App Installation ID)
- GITHUB_WEBHOOK_SECRET (GitHub App webhook secret)
- GITHUB_PRIVATE_KEY_PATH (path to the GitHub App private key PEM)
- KIMI_API_KEY (Moonshot Kimi via LiteLLM)

Optional:
- KIMI_API_BASE_URL (override LiteLLM base URL)
- INIT_DB_ON_STARTUP ("true" by default)
- GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET (OAuth flows for frontend login)
- JWT_SECRET_KEY (required when issuing auth cookies)

## GitHub App setup (summary)

1) Create a GitHub App, enable Pull request events, set the Webhook URL to `https://<your-domain>/webhook` and configure the same `GITHUB_WEBHOOK_SECRET`.
2) Install the App to your repository and note the installation ID (`GITHUB_INSTALLATION_ID`).
3) Download the private key and set `GITHUB_PRIVATE_KEY_PATH` to its location.

## Notes

- Run `uv run uvicorn server:app` from the `backend` folder so imports resolve correctly.
- Incoming `/webhook` requests must include the `X-Hub-Signature-256` header signed with `GITHUB_WEBHOOK_SECRET`.
- The server currently responds with a comment on PR events (`opened`, `reopened`, `synchronize`).
