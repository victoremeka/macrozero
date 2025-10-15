from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.genai import types
from google.adk.sessions import InMemorySessionService
from agents.tools import model, create_pr_review
import json
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)

from agents.agents import (
    memory_agent,
    issue_triage_resolution_agent,
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
    - Pass only: owner, repo, number (PR/issue), body, and diff if available.
    - Do not select internal step agents (names starting with `_step_`). Only choose from: code_review_agent, issue_triage_agent, research_agent.
    - Do NOT route GitHub webhooks to db_admin_agent/memory_agent. That agent is reserved for explicit database/vector memory tasks (e.g., "search memory", "similar PRs", migrations).

    Pass the final result to `handoff_data`
    """,
    sub_agents=[
        memory_agent,
        issue_triage_resolution_agent,
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

    payload_json = json.dumps(payload, ensure_ascii=False)
    content = types.Content(
        role="user",
        parts=[types.Part(text=f"GitHub webhook context:\n{payload_json}")]
    )

    final_response_text = "Agent produced no final response."

    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
        is_final = getattr(event, "is_final_response", lambda: False)()

        if is_final:
            evt_content = getattr(event, "content", None)
            text_val = None
            if evt_content is not None:
                content_dict = getattr(evt_content, "__dict__", {})
                maybe_parts = content_dict.get("parts")
                if isinstance(maybe_parts, list) and len(maybe_parts) > 0:
                    first_part = maybe_parts[0]
                    part_dict = getattr(first_part, "__dict__", {})
                    candidate_text = part_dict.get("text")
                    if isinstance(candidate_text, str):
                        text_val = candidate_text

            if isinstance(text_val, str) and text_val:
                final_response_text = text_val
            elif getattr(event, "actions", None) and getattr(event.actions, "escalate", False):
                final_response_text = (
                    f"Agent escalated: {getattr(event, 'error_message', None) or 'No specific message.'}"
                )
            else:
                # Fallback to stringified event
                final_response_text = str(getattr(event, "message", "")) or str(event)
    try:
        text = str(final_response_text or "").strip()
        json_start = text.find("{")
        json_end = text.rfind("}")
        parsed = None
        if json_start != -1 and json_end != -1 and json_end > json_start:
            candidate = text[json_start:json_end + 1]
            try:
                parsed = json.loads(candidate)
            except json.JSONDecodeError:
                # Try raw text as a last resort
                parsed = json.loads(text)

        if isinstance(parsed, dict):
            required = {"owner", "repo", "number", "body", "event"}
            if required.issubset(parsed.keys()):
                comments = parsed.get("comments") or []
                filtered: list[dict] = []
                seen: set[tuple] = set()
                for c in comments:
                    if not isinstance(c, dict):
                        continue
                    path = c.get("path")
                    body = c.get("body")
                    line = c.get("line")
                    side = c.get("side") or "RIGHT"
                    start_line = c.get("start_line")
                    start_side = c.get("start_side")
                    if path and body and isinstance(line, int):
                        key = (path, line, side)
                        if key in seen:
                            continue
                        item = {"path": path, "line": line, "side": side, "body": body}
                        if isinstance(start_line, int):
                            item["start_line"] = start_line
                            item["start_side"] = start_side or side
                        filtered.append(item)
                        seen.add(key)

                try:
                    resp = create_pr_review(
                        owner=parsed["owner"],
                        repo=parsed["repo"],
                        number=int(parsed["number"]),
                        body=parsed.get("body", ""),
                        comments=filtered,
                        event=parsed.get("event", "COMMENT"),
                    )
                    logging.info("Server-side fallback posted review: %s", str(resp)[:500])
                except Exception as post_err:
                    logging.error("Server-side fallback failed to post review: %s", post_err)
    except Exception as parse_err:
        logging.debug("No server-side fallback applied: %s", parse_err)

    return final_response_text
