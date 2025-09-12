from google.adk import Agent, Runner
from agents.agents import *

orchestrator_agent = Agent(
    name="Orchestrator Agent",
    sub_agents=[
        auto_fix_agent,
        db_admin_agent,
        issue_triage_agent,
        memory_agent,
        research_agent,
        reviewer_agent,
        sanitizer_agent,
    ]
)