from google.adk.sessions import DatabaseSessionService, InMemorySessionService
from db import get_db_url

def get_agent_session(test=True):
    if test:
        return InMemorySessionService()
    return DatabaseSessionService(str(get_db_url()))