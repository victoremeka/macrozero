from typing import Literal
from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import InMemoryRunner, Runner
from google.adk.sessions import InMemorySessionService, DatabaseSessionService
from google.genai import types
from pydantic import BaseModel, Field
import dotenv
import os

dotenv.load_dotenv()

with open("agents/code_review_prompt.txt", "r", encoding="utf-8") as f:
    review_prompt = f.read()

with open("agents/technical_summary_prompt.txt", "r", encoding="utf-8") as f:
    summary_prompt = f.read()

class ReviewComment(BaseModel):
    path: str = Field(description="The file path")
    position: int = Field(description="The line position in the diff (starting from 1 after each @@ hunk header)")
    body: str = Field(description="The review comment")

class CodeReview(BaseModel):
    body: str = Field(description="Overall review summary with merge recommendation")
    event: Literal["APPROVE", "REQUEST_CHANGES", "COMMENT"] = Field(description="The review action")
    comments: list[ReviewComment] = Field(description="List of review comments")

summarizer_agent = LlmAgent(
    model=LiteLlm(model="gemini/gemini-2.5-flash-lite"),
    name="code_review_agent",
    instruction=summary_prompt,
    output_key='technical_summary'
)

reviewer_agent = LlmAgent(
    model=LiteLlm(model="gemini/gemini-2.5-flash"),
    name="code_review_agent",
    instruction=review_prompt,
    output_schema=CodeReview
)

APP_NAME = "macrozeroai"

DATABASE_URL = os.getenv("DB_URL")
DATABASE_PASSWORD = os.getenv("DB_PASSWORD")

async def call_agent(agent, query, session_service, app_name, user_id, session_id):
    """Helper to call a single agent and get its response"""
    runner = Runner(agent=agent, app_name=app_name, session_service=session_service)
    content = types.Content(role='user', parts=[types.Part(text=query)])
    events = runner.run(user_id=user_id, session_id=session_id, new_message=content)

    for event in events:
        if event.is_final_response() and event.content:
            return event.content.parts[0].text.strip()
    return None

async def review_pr(pr_files: str, diff: str, user_id: str):
    session_service = DatabaseSessionService(DATABASE_URL) if DATABASE_URL else InMemorySessionService()
    session = await session_service.create_session(app_name=APP_NAME, user_id=user_id)
    technical_summary = await call_agent(summarizer_agent, pr_files, session_service, app_name=APP_NAME, user_id=user_id, session_id=session.id)

    review_query = f"{diff}\n\n--- TECHNICAL SUMMARY ---\n{technical_summary}"
    review_result = await call_agent(reviewer_agent, review_query, session_service, app_name=APP_NAME, user_id=user_id, session_id=session.id)

    return review_result
