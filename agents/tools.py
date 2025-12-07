"""Agent-accessible tools for GitHub interactions and search.

Exposes:
    create_pr_review: Submit a GitHub pull request review with optional inline comments.
    mcp_tools: Filtered MCP toolset for selected GitHub operations.
    search_tool: Agent tool wrapping a Google search specialist agent.
"""

from integrations.github_client import *
from typing import Literal
from google.adk.tools import google_search
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools.mcp_tool import MCPToolset, StreamableHTTPConnectionParams
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
import os, dotenv


dotenv.load_dotenv()

model = "gemini-2.5-pro"

def create_pr_review(owner: str, repo: str, number: int, body: str, comments: list[dict], event: Literal["COMMENT","REQUEST_CHANGES","APPROVE"] = "COMMENT"):
    """Create a pull request review.

    Args:
        owner: Repository owner login.
        repo: Repository name.
        number: Pull request number.
        body: Overall review body text.
        comments: Inline comment dicts per GitHub API (path, position/line, body, etc.).
        event: Review action: COMMENT (default), REQUEST_CHANGES, APPROVE.

    Returns:
        dict: GitHub API JSON response.
    """
    payload = {
        "body": body,
        "event": event,
        "comments": comments,
    }

    resp = gh_json(
        method="post",
        path=f"/repos/{owner}/{repo}/pulls/{number}/reviews",
        json=payload,
        headers={"Accept": "application/vnd.github+json"},
    )
    return resp



search_agent = Agent(
    model=model,
    name="search_agent",
    instruction="""
    You're a specialist in Google Search.
    """,
    tools=[google_search],
)
search_tool = AgentTool(search_agent)
