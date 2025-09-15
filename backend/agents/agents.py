import dotenv
import asyncio
from google.adk.agents import Agent, SequentialAgent

from pydantic import BaseModel, Field

from .prompts import review_prompt       
from .tools import create_pr_review, model     


reviewer_agent = Agent(
    name="reviewer_agent",
    model=model,
    description="Writes and submits GitHub PR reviews.",
    instruction=review_prompt,
    output_key="review"
)

sanitizer_agent = Agent(
    name="sanitizer_agent",
    model=model,
    description="Cleans and formats code diffs and patches before submission.",
    instruction="""
    Read in the data from {review}
    and adapt it to the following example function call:
    create_pr_review(
        owner=repo_owner,
        repo=repo_name,
        number=pull_request_number,
        body="This is a test review with Macrozero app",
        event="COMMENT",
        comments=[
            {
                "path": "main.py",
                "position": int(diff[0][0])+1,
                "body": "```suggestion\nprint(\"Hello from agent!\")\n```"
                
            }
        ]
    )
    """,
    tools=[create_pr_review]
)

code_review_agent = SequentialAgent(
    name="code_review_agent",
    description="Code review multi agent system",
    sub_agents=[reviewer_agent, sanitizer_agent]
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