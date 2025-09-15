from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from sqlmodel import Session
from db import create_db_and_tables, get_session
from agents.session_service import get_agent_session_service
from apis.github_webhook import handle_webhook_payload
from routers.auth import get_current_user, router as auth_router
from google.adk.sessions import DatabaseSessionService, InMemorySessionService


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield
    print("Application shutdown: Cleaning up resources...")
    # Example: Close the database connection
    # await db_connection.close()


app = FastAPI(lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# Include routers
app.include_router(auth_router)


@app.post("/webhook")
async def webhook(
    request: Request, 
    session : Session = Depends(get_session), 
    agent_session : DatabaseSessionService | InMemorySessionService = Depends(get_agent_session_service)
    ):
    
    await handle_webhook_payload(request, session, agent_session)

# Example protected route
@app.get("/protected")
async def protected_route(current_user: dict = Depends(get_current_user)):
    return {"message": "This is a protected route", "user": current_user}


# Example optional auth route
@app.get("/")
async def root(current_user: dict = Depends(get_current_user)):
    if current_user:
        return {"message": f"Hello {current_user.get('username', 'User')}!"}
    return {"message": "Hello Guest!"}
