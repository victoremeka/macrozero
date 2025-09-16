from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os, logging

from sqlmodel import Session
from db import create_db_and_tables, get_session
from apis.github_webhook import handle_webhook_payload
from routers.auth import get_current_user, router as auth_router
from google.adk.sessions import DatabaseSessionService, InMemorySessionService


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Optionally initialize DB schema on startup; avoid blocking Cloud Run if DB is unreachable
    if os.getenv("INIT_DB_ON_STARTUP", "true").lower() in {"1", "true", "yes"}:
        try:
            create_db_and_tables()
        except Exception as e:
            logging.warning("DB init skipped due to error: %s", e)
    yield
    print("Application shutdown: Cleaning up resources...")

app = FastAPI(lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "https://macrozero.vercel.app/", "https://macrozero-backend-359934259952.europe-west1.run.app"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# Include routers
app.include_router(auth_router)
# Lightweight health endpoint (no auth, no DB)
@app.get("/healthz")
async def healthz():
    return {"status": "ok"}



@app.post("/webhook")
async def webhook(request: Request, session : Session = Depends(get_session)):
    
    await handle_webhook_payload(request, session)

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
