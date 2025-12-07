from typing import Literal
from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService, DatabaseSessionService
from google.genai import types
from pydantic import BaseModel, Field

with open("agents/code_review_prompt.txt", "r", encoding="utf-8") as f:
    base_prompt = f.read()

class ReviewComment(BaseModel):
    path: str = Field(description="The file path")
    position: int = Field(description="The line position in the diff (starting from 1 after each @@ hunk header)")
    body: str = Field(description="The review comment")

class CodeReview(BaseModel):
    body: str = Field(description="Overall review summary with merge recommendation")
    event: Literal["APPROVE", "REQUEST_CHANGES", "COMMENT"] = Field(description="The review action")
    comments: list[ReviewComment] = Field(description="List of review comments")

agent = LlmAgent(
    model=LiteLlm(model="gemini/gemini-2.5-flash"),
    name="code_review_agent",
    instruction=base_prompt,
    output_schema=CodeReview
)

APP_NAME = "macrozeroai"
USER_ID = "local123"
SESSION_ID = "session123"

TEST_MODE = True
db_url = ""
async def call_agent(query):
    session_service = InMemorySessionService() if TEST_MODE else DatabaseSessionService("sqlite:///data.db")
    session = await session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)  # pyright: ignore[reportCallIssue]
    runner = Runner(agent=agent, app_name=APP_NAME, session_service=session_service)  # pyright: ignore[reportArgumentType]

    content = types.Content(role='user', parts=[types.Part(text=query)])
    events = runner.run(user_id=USER_ID, session_id=SESSION_ID, new_message=content)

    for event in events:
        if event.is_final_response() and event.content:
            final_answer = event.content.parts[0].text.strip()
            return final_answer
