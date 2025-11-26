# Contributing to Macrozero

Thanks for wanting to contribute. Here's how to get started.

## Dev setup

Prerequisites: Python 3.13+, [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/yourusername/macrozero.git
cd macrozero/app
uv sync
```

Copy `.env.example` to `.env` and fill in your keys:
```
GITHUB_APP_ID=...
GITHUB_INSTALLATION_ID=...
GITHUB_WEBHOOK_SECRET=...
GITHUB_PRIVATE_KEY=...
GEMINI_API_KEY=...
```

Run it:
```bash
uv run uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

## GitHub App setup

You'll need a GitHub App to test webhooks locally.

1. Go to GitHub Settings → Developer settings → GitHub Apps → New GitHub App
2. Enable these events: pull requests, issues, pull request reviews
3. Set webhook URL to `https://<your-ngrok-or-local-tunnel>/listen`
4. Generate a webhook secret, use it for `GITHUB_WEBHOOK_SECRET`
5. After creating, note the App ID → `GITHUB_APP_ID`
6. Generate a private key, save it, set path in `GITHUB_PRIVATE_KEY`
7. Install the app on a test repo, grab the installation ID from the URL

For local testing, use [ngrok](https://ngrok.com/) or similar to expose port 8000.

## Project structure

```
macrozero/
├── app/                    # Main Python service
│   ├── agents/            # AI agent definitions
│   │   ├── agents.py      # Reviewer, sanitizer, research agents
│   │   ├── prompts.py     # Agent instructions
│   │   └── tools.py       # GitHub API tools + search
│   ├── app/               # Core webhook handling
│   │   ├── agent.py       # Legacy agent (being phased out)
│   │   ├── github_webhook.py  # Webhook verification + routing
│   │   └── pr_handler.py  # PR event processing
│   ├── integrations/      # External API clients
│   │   └── github_client.py  # GitHub API wrapper
│   ├── models.py          # Database models
│   ├── db.py              # Database operations
│   └── server.py          # FastAPI app entry point
└── pr-handler/            # Go webhook router (optional)
```

## How the code works

### Webhook flow
1. GitHub sends event → `/listen` endpoint (server.py)
2. `github_webhook.py` verifies signature, routes to handler
3. `pr_handler.py` fetches diff, calls agent system
4. Agents analyze → package → submit review via GitHub API

### Agent system
Built on Google ADK. Three agents in sequence:
- **Reviewer**: Analyzes code, finds issues
- **Sanitizer**: Converts analysis to GitHub PR review format
- **Research**: (Future) Searches for similar issues/fixes

Each agent gets the previous output as context.

### Database
Tracks repos, PRs, commits, reviews. SQLModel + TiDB support.
Currently just for user entities. May expand to store diffs for RAG later.

## Making changes

### Adding a new agent
1. Define it in `agents/agents.py`
2. Add its prompt in `agents/prompts.py`
3. Wire it into the SequentialAgent chain

### Modifying review logic
Edit `agents/prompts.py` → `review_prompt` or `pr_review_packaging_prompt`.
The agents follow these instructions strictly.

### Adding GitHub API calls
Add functions to `integrations/github_client.py`.
Use `gh_json()` for authenticated requests.

## Code style

- Keep it simple. No over-engineering.
- Functions should be short and obvious.
- Comments only when the "why" isn't clear.
- Run commands from `app/` so imports resolve.

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

**Imports not resolving**: Run commands from `app/` directory.

**Webhook signature fails**: Check `GITHUB_WEBHOOK_SECRET` matches your App.

**Agent doesn't call tools**: Check tool definitions in `agents/tools.py`. Google ADK can be picky about schemas.

**Review not appearing**: Check logs. Likely a GitHub API error (wrong permissions, bad token, etc).

## Database

Currently using SQLite (`database.db` in root). For production, point to TiDB or MySQL:

```python
# db.py uses this env var format
DATABASE_URL = "mysql+pymysql://user:pass@host:port/db"
```

The schema auto-creates on first run via SQLModel.

## Future work

- RAG retrieval from past commits/reviews
- Issue auto-fix (research agent + PR creation)
- Frontend for managing repos/settings
- Support more models (OpenAI, Anthropic, etc)
- Async queue processing (currently blocking)

## Questions?

Open an issue or PR. We're friendly.