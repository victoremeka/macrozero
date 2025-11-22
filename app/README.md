# macrozero code review service
This is where the not so magic-magic happens.

## Setup

Prerequisites: Python 3.13+, [uv](https://docs.astral.sh/uv/).

```bash
cd app
uv sync
uv run uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

## Operational notes
- Run commands from `app/` so imports resolve.
- Webhook processing currently handles PR, PR review, and issue events; review comments are ignored.
- All webhook requests must include `X-Hub-Signature-256` signed with `GITHUB_WEBHOOK_SECRET`.
