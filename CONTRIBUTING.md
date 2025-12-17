# Contributing to Macrozero

Thanks for wanting to contribute. Here's how to get started.

## Dev setup

Prerequisites: Python 3.13+, [uv](https://docs.astral.sh/uv/), a GitHub App, Gemini API key.

```bash
git clone https://github.com/yourusername/macrozero.git
cd macrozero
uv sync
```

Copy `.env.example` to `.env` and fill in your keys:
```
GITHUB_APP_ID=...
GITHUB_WEBHOOK_SECRET=...
GITHUB_PRIVATE_KEY=...
GEMINI_API_KEY=...
DB_URL=...  # optional, for persistent session storage
```

Run it:
```bash
uv run uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

## GitHub App setup

You'll need a GitHub App to test webhooks locally.

1. Create an App, enable pull request events, set webhook to `https://<your-domain>/listen`
2. Use the same secret for the App and `GITHUB_WEBHOOK_SECRET`
3. Install the App on your target repository
4. Drop your private key in the env

For local testing, use [ngrok](https://ngrok.com/) or similar to expose port 8000.

## Project structure

```
macrozero/
├── agents/                     # AI agent definitions
│   ├── agents.py               # Summarizer and reviewer agents
│   ├── code_review_prompt.txt  # Reviewer agent instructions
│   ├── code_review_instructions.md  # Additional review guidelines
│   └── technical_summary_prompt.txt  # Summarizer agent instructions
├── integrations/               # External API clients
│   └── github_client.py        # GitHub API wrapper (JWT, tokens)
├── payloads/                   # Debug payload dumps
├── github_webhook.py           # Webhook verification + routing
├── pr_handler.py               # PR event processing
├── server.py                   # FastAPI app entry point
├── Dockerfile                  # Container build
└── pyproject.toml              # Dependencies
```

## How the code works

### Webhook flow
1. GitHub sends event → `/listen` endpoint (`server.py`)
2. `github_webhook.py` verifies signature, routes to handler
3. `pr_handler.py` fetches diff and full file contents
4. Agents analyze → structured review → submit via GitHub API

### Agent system
Built on Google ADK with LiteLLM. Two agents in sequence:
- **Summarizer**: Creates a technical summary of all changed files (uses `gemini-2.5-flash-lite`)
- **Reviewer**: Analyzes the diff with the summary as context, outputs structured `CodeReview` with line comments (uses `gemini-2.5-flash`)

The reviewer outputs a Pydantic model (`CodeReview`) containing:
- `body`: Overall review summary
- `event`: `APPROVE`, `REQUEST_CHANGES`, or `COMMENT`
- `comments`: List of line-specific comments with file path and diff position

### Session storage
By default, uses in-memory sessions. Set `DB_URL` to use `DatabaseSessionService` for persistence.

## Making changes

### Modifying review behavior
Edit the prompt files in `agents/`:
- `code_review_prompt.txt` - Main reviewer instructions
- `technical_summary_prompt.txt` - Summarizer instructions

### Adding a new agent
1. Define it in `agents/agents.py` using `LlmAgent`
2. Add its prompt file in `agents/`
3. Wire it into `review_pr()` using the `call_agent()` helper

### Adding GitHub API calls
Add functions to `integrations/github_client.py`. Use `_installation_token()` for authenticated requests.

## Code style

- Keep it simple. No over-engineering.
- Functions should be short and obvious.
- Comments only when the "why" isn't clear.

## Testing locally

1. Install your GitHub App on a test repo
2. Open a PR
3. Watch the logs: `uv run uvicorn server:app --reload`
4. Check if the review appears on the PR

No formal test suite yet. We rely on dogfooding (using Macrozero to review Macrozero).

## Submitting PRs

1. Fork the repo
2. Make your changes in a branch
3. Open a PR with a clear description
4. Macrozero will review it (meta!)
5. Address feedback, merge

## Common issues

**Webhook signature fails**: Check `GITHUB_WEBHOOK_SECRET` matches your App.

**Review not appearing**: Check logs. Likely a GitHub API error (wrong permissions, bad token, etc).

**Agent output not parsing**: The reviewer uses a Pydantic output schema. Check that the model is returning valid JSON matching the `CodeReview` schema.

**Diff position wrong**: The `position` field is the line number in the diff (after `@@` hunk headers), not the file line number. See `format_diff()` in `pr_handler.py`.

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GITHUB_APP_ID` | Yes | Your GitHub App ID |
| `GITHUB_WEBHOOK_SECRET` | Yes | Webhook secret for signature verification |
| `GITHUB_PRIVATE_KEY` | Yes | Private key for GitHub App authentication |
| `GEMINI_API_KEY` | Yes | Google Gemini API key |
| `DB_URL` | No | Database URL for persistent sessions (e.g., `mysql+pymysql://...`) |

## Future work

- RAG retrieval from past commits/reviews
- Support more models (OpenAI, Anthropic, etc)
- Async queue processing (currently blocking)
- Frontend for managing repos/settings

## Questions?

Open an issue or PR. We're friendly.