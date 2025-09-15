from google.adk.sessions import DatabaseSessionService, InMemorySessionService

from db import get_db_url

session_service = InMemorySessionService() # DatabaseSessionService(str(get_db_url())) for prod


def get_agent_session_service(test=True):
    return session_service
