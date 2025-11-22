from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService, DatabaseSessionService
from google.genai import types

with open("app/code_review_prompt.txt", "r", encoding="utf-8") as f:
    base_prompt = f.read()


agent = LlmAgent(
    model=LiteLlm(model="gemini/gemini-2.5-flash"), # LiteLLM model string format
    name="code_review_agent",
    instruction=base_prompt,
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
