import os
import dotenv
import asyncio
from google.adk.agents import Agent, SequentialAgent
from google.adk.models.lite_llm import LiteLlm

from pydantic import BaseModel, Field

from .prompts import review_prompt            
from .tools import create_pr_review           
from integrations.github_client import use_installation

dotenv.load_dotenv()

KIMI_API_KEY = os.getenv("KIMI_API_KEY")
KIMI_API_BASE_URL = os.getenv("KIMI_API_BASE_URL")


model = LiteLlm(
    model="moonshot/kimi-k2-0905-preview",
    api_key=KIMI_API_KEY,            
    base_url=KIMI_API_BASE_URL,
)

reviewer_agent = Agent(
    name="reviewer_agent",
    model=model,
    description="Writes and submits GitHub PR reviews.",
    instruction=review_prompt.format(
        code=""
    ),
    tools=[create_pr_review],
)

code_sanitizer_agent = Agent(
    name="sanitizer_agent",
    model=model,
    description="Cleans and formats code diffs and patches before submission.",
)

issue_triage_agent = Agent(
    name="issue_triage_agent",
    model=model,
    description="Triages issues and extracts repro/owners/severity.",
)

db_admin_agent = Agent(
    name="db_admin_agent",
    model=model,
    description="Maintains embeddings DB and migrations.",
)

research_agent = Agent(
    name="research_agent",
    model=model,
    description="Searches prior fixes and summarizes findings.",
)