import os
import openai
import dotenv
from google.adk.agents import Agent, SequentialAgent
from google.adk.models.lite_llm import LiteLlm
from agents.prompts import *

dotenv.load_dotenv()

KIMI_API_KEY = os.getenv("KIMI_API_KEY")
KIMI_API_BASE_URL = os.getenv("KIMI_API_BASE_URL")

model = LiteLlm(
    model="moonshot/kimi-k2-0905-preview", 
)

reviewer_agent = Agent(
    name="reviewer_agent",
    model=model,
    description="",
    instruction=review_prompt,
)

auto_fix_agent = Agent(
    name="auto_fix_agent",
    model=model,
    instruction="",
    tools=[],
)

sanitizer_agent = Agent(
    name="sanitizer_agent",
    model=model
)


memory_agent = Agent(
    name="memory_agent",
    model=model,
)


issue_triage_agent = Agent(
    name="issue_triage_agent",
    model=model,
)

db_admin_agent = Agent(
    name="db_admin_agent",
    model=model,
)

research_agent = Agent(
    name="research_agent",
    model=model,
)