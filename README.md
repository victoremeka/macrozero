# macrozero

Multi-agent system that summarizes GitHub bugs, drafts PRs, reviews code, and recalls past fixes.

## Setup

```bash
cd backend
uv sync
uv run uvicorn backend.server:app --reload
```

**Requirements:** Python 3.13+
