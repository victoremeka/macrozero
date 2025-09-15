from google.adk.runners import Runner
from google.adk import Agent
from google.adk.memory import InMemoryMemoryService
from google.adk.sessions import BaseSessionService

    
class RootAgentRunner():
    def __init__(self, app_name: str, agent: Agent, session_service: BaseSessionService, memory_service: InMemoryMemoryService = InMemoryMemoryService()) -> None:
        self.root_agent_runner = Runner(
            app_name=app_name,
            agent=agent,
            session_service=session_service,
            memory_service=memory_service,
    )
        
    def _get_runner(self):
        return self.root_agent_runner