from integrations.github_client import *
from typing import Literal
from google.adk.tools import google_search
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools.mcp_tool import MCPToolset, StreamableHTTPConnectionParams
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
import os, dotenv


dotenv.load_dotenv()

KIMI_API_KEY = os.getenv("KIMI_API_KEY")
KIMI_API_BASE_URL = os.getenv("KIMI_API_BASE_URL")

model = LiteLlm(
    model="moonshot/kimi-k2-0905-preview",
    api_key=KIMI_API_KEY,            
    base_url=KIMI_API_BASE_URL,
)

mcp_tools = MCPToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="https://api.githubcopilot.com/mcp/",
        headers={
            "Authorization": "Bearer " + os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN"),
        },
    ),

    tool_filter=[
        "search_repositories",
        "search_issues",
        "list_issues",
        "get_issue",
        "list_pull_requests",
        "get_pull_request",
    ],
)

def create_pr_review(owner: str, repo: str, number: int, body: str, comments: list[dict], event: Literal["COMMENT","REQUEST_CHANGES","APPROVE"] = "COMMENT"):
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