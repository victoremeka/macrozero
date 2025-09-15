from google.adk import Agent, Runner
from agents.session_service import get_agent_session
from agents.agents import (
    db_admin_agent,
    issue_triage_agent,
    research_agent,
    reviewer_agent,
    code_sanitizer_agent,
)

orchestrator_agent = Agent(
    name="Orchestrator Agent",
    instruction="""
    Handoff to the appropriate agent for the request.

    """
    sub_agents=[
        db_admin_agent,
        issue_triage_agent,
        research_agent,
        reviewer_agent,
        code_sanitizer_agent,
    ]
)
APP_NAME = "macrozero"
session = get_agent_session()

root_agent_runner = Runner(
    app_name=APP_NAME,
    agent=orchestrator_agent,
    session_service=session
)

async def call_agent_async(data: str, runner: Runner, user_id: str, session_id: str):
    
    content = 