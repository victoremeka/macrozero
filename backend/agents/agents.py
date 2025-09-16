from google.adk.agents import Agent, SequentialAgent

from .prompts import review_prompt, pr_review_packaging_prompt       
from .tools import create_pr_review, model     


reviewer_agent = Agent(
    name="_step_reviewer",
    model=model,
    description="Writes and submits GitHub PR reviews.",
    instruction=review_prompt,
    output_key="review"
)

sanitizer_agent = Agent(
    name="_step_packager",
    model=model,
    description="Transforms raw review analysis into a valid GitHub PR review JSON and submits it.",
    instruction=pr_review_packaging_prompt,
    tools=[create_pr_review]
)

code_review_agent = SequentialAgent(
    name="code_review_agent",
    description="Code review multi agent system",
    sub_agents=[reviewer_agent, sanitizer_agent],
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