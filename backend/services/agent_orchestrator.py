from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.genai import types
from google.adk.sessions import InMemorySessionService, DatabaseSessionService
from agents.tools import model
# import logging

# logging.basicConfig(
#     level=logging.DEBUG,
#     format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
# )

from agents.agents import (
    db_admin_agent,
    issue_triage_agent,
    research_agent,
    code_review_agent,
)

orchestrator_agent = LlmAgent(
    name="orchestrator_agent",
    model=model,
    description="An orchestrator for the multi-agent system",
  instruction="""
    You are an orchestration agent.
    You receive GitHub webhooks. Route to exactly one sub-agent. Do not solve tasks yourself.

    Routing:
  - pull_request* -> code_review_agent (this agent internally runs two steps: reviewer then packager)
  - issues* -> issue_triage_agent
  - otherwise -> research_agent

    Behavior:
  - No questions. If required fields are missing, respond: missing <fields>.
  - Pass only: owner, repo, number (PR/issue), title, body, and diff if available.
  - Do not select internal step agents (names starting with `_step_`). Only choose from: code_review_agent, issue_triage_agent, research_agent, db_admin_agent.

    Pass the final result to `handoff_data`
    """,
    sub_agents=[
        db_admin_agent,
        issue_triage_agent,
        research_agent,
        code_review_agent,
    ],
    output_key="handoff_data"
)
root_agent = orchestrator_agent
APP_NAME = "macrozero"
session_service = InMemorySessionService()

runner = Runner(
   agent=root_agent,
   app_name=APP_NAME,
   session_service=session_service
)

async def call_agent_async(payload: dict, user_id: str, session_id: str):
    session = await session_service.get_session(
        app_name=APP_NAME,
        user_id=user_id,
        session_id=session_id,
    ) or await session_service.create_session(
        app_name=APP_NAME,
        user_id=user_id,
        session_id=session_id,
    )

    content = types.Content(
        role="user",
        parts=[types.Part(text=f"GitHub webhook context:\n{payload}")]
    )

    final_response_text = "Agent produced no final response."

    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
        # emitter = getattr(event, "author", None) or getattr(event, "agent_name", None)
        is_final = getattr(event, "is_final_response", lambda: False)()

        # logging.debug(f"Runner event: emitter={emitter} is_final={is_final}")

        if is_final:
            if getattr(event, "content", None) and event.content.parts:
                final_response_text = event.content.parts[0].text
            elif getattr(event, "actions", None) and getattr(event.actions, "escalate", False):
                final_response_text = (
                    f"Agent escalated: {getattr(event, 'error_message', None) or 'No specific message.'}"
                )
    print("FINAL RESPONSE IN CALL_AGENT_ASYNC -->", final_response_text)
    return final_response_text