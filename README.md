# Macrozero
AI code reviews that actually understand your codebase.

Model agnostic. Codebase aware. Built for OSS.

## Setup

Prerequisites: Python 3.13+, [uv](https://docs.astral.sh/uv/), a GitHub App, Gemini API key.

```bash
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


## Docker
```bash
cd app
docker build -t macrozero .
docker run -p 8000:8000 --env-file .env macrozero
```

## Contributing
See `CONTRIBUTING.md` for dev setup and contribution guidelines.
