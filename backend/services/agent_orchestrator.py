from google.adk import Agent
from google.adk.runners import Runner
from google.genai import types


from agents.agents import (
    db_admin_agent,
    issue_triage_agent,
    research_agent,
    code_review_agent,
)

orchestrator_agent = Agent(
    name="orchestrator_agent",
    description="",
    instruction="""
    You are an orchestrator agent.
    You receive GitHub webhooks. Route to exactly one sub-agent. Do not solve tasks yourself.

    Routing:
    - pull_request* -> code_review_agent
    - issues* -> issue_triage_agent
    - sanitize/patch requests -> code_sanitizer_agent
    - otherwise -> research_agent

    Behavior:
    - No questions. If required fields are missing, respond: missing <fields>.
    - Pass only: owner, repo, number (PR/issue), installation_id, title, body, and diff if available.
    """,
    sub_agents=[
        db_admin_agent,
        issue_triage_agent,
        research_agent,
        code_review_agent,
    ]
)

async def call_agent_async(payload: dict, runner: Runner, user_id: str, session_id: str, is_pr: bool = True):

    content = types.Content(
       role='user', 
       parts=[types.Part(text=f"GitHub webhook context:\n{payload}")]
    )
    
    final_response_text = "Agent produced no final response."
    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
        if event.is_final_response():
          if event.content and event.content.parts:
            final_response_text = event.content.parts[0].text
          elif event.actions and event.actions.escalate:
            final_response_text = f"Agent escalated: {event.error_message or 'No specific message.'}"
          break
    
    print("RUNNING IN CALL_AGENT_ASYNC -->", final_response_text)
    return final_response_text