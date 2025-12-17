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
1. Create an App, enable pull request events, set webhook to `https://<your-domain>/listen`
2. Use the same secret for the App and `GITHUB_WEBHOOK_SECRET`
3. Install the App on your target repository
4. Drop your private key in the env

### Environment variables
```
GITHUB_APP_ID=...
GITHUB_WEBHOOK_SECRET=...
GITHUB_PRIVATE_KEY=...
GEMINI_API_KEY=...
DB_URL=...  # optional, for persistent session storage
```

## What makes it good
- Every issue references a specific line in the diff—no vague feedback
- Evaluates correctness, readability, maintainability, performance, security
- Generates GitHub suggestion blocks (one-click fixes)
- Two-agent system: one summarizes, one reviews
- Webhook signature verification (secure by default)

## How it works
1. GitHub sends a pull request event to `/listen`
2. Webhook signature is verified
3. Summarizer agent creates a technical summary of the changed files
4. Reviewer agent analyzes the diff with the summary as context
5. Structured review (with line comments) is posted back to the PR

## Docker
```bash
docker build -t macrozero .
docker run -p 8000:8000 --env-file .env macrozero
```

## Contributing
See `CONTRIBUTING.md` for dev setup and contribution guidelines.