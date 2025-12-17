# Contributing to Macrozero

## Dev setup

Prerequisites: Python 3.13+, [uv](https://docs.astral.sh/uv/), a GitHub App, Gemini API key.

```bash
git clone https://github.com/yourusername/macrozero.git
cd macrozero
uv sync
cp .env.example .env  # fill in your keys
uv run uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

For local webhook testing, use [ngrok](https://ngrok.com/) to expose port 8000.

## How it works

1. GitHub sends PR event → `server.py` → `github_webhook.py` verifies signature
2. `pr_handler.py` fetches diff and file contents
3. Summarizer agent creates technical summary, reviewer agent analyzes with structured output
4. Review posted back to PR via GitHub API

## Making changes

**Review behavior**: Edit prompts in `agents/*.txt`

**New agent**: Add to `agents/agents.py`, wire into `review_pr()`

**GitHub API**: Add to `integrations/github_client.py`

## Testing

1. Install your GitHub App on a test repo
2. Open a PR
3. Watch logs, check if review appears

## Common issues

- **Webhook signature fails**: `GITHUB_WEBHOOK_SECRET` doesn't match your App
- **Review not appearing**: Check logs for GitHub API errors
- **Agent output not parsing**: Model not returning valid JSON for `CodeReview` schema
- **Wrong line position**: `position` is diff line number (after `@@`), not file line number