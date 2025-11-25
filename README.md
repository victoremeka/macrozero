# Macrozero
AI code reviews that actually understand your codebase.

## What is this?
A GitHub App that reviews your pull requests. Not the generic "consider adding tests" kind—actual specific feedback tied to your code.

Model agnostic. Codebase aware. Built with agents.

## How it works
1. You open a PR
2. Macrozero fetches the diff
3. AI agents analyze it (reviewer → packager → submitter)
4. You get inline comments on specific lines, plus an overall review
5. It auto-decides whether to approve, comment, or request changes

## Setup

Prerequisites: Python 3.13+, [uv](https://docs.astral.sh/uv/), a GitHub App, Gemini API key.

```bash
cd app
uv sync
cp .env.example .env  # fill in your keys
uv run uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

### GitHub App setup
1. Create an App, enable pull request + issue events, set webhook to `https://<your-domain>/listen`
2. Use the same secret for the App and `GITHUB_WEBHOOK_SECRET`
3. Install the App, grab the installation ID
4. Drop your private key in the env

### Environment variables
```
GITHUB_APP_ID=...
GITHUB_INSTALLATION_ID=...
GITHUB_WEBHOOK_SECRET=...
GITHUB_PRIVATE_KEY=...
GEMINI_API_KEY=...
```

## What makes it good
- Every issue references a specific line/function/variable—no vague feedback
- Evaluates correctness, readability, maintainability, performance, security
- Generates GitHub suggestion blocks (one-click fixes)
- Multi-agent system: one reviews, one packages, one researches
- Webhook signature verification (secure by default)

## Architecture
Two pieces:
- **`/app`**: FastAPI + Google ADK agents. Does the actual review work.
- **`/pr-handler`**: Go webhook router. Lightweight queue handler.

Run commands from `app/` so imports resolve.

## Docker
```bash
cd app
docker build -t macrozero .
docker run -p 8000:8000 --env-file .env macrozero
```

## Contributing
See `CONTRIBUTING.md` for dev setup and contribution guidelines.