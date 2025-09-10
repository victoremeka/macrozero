from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from db import create_db_and_tables
from apis.github_webhook import (
    handle_webhook_payload
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield
    print("Application shutdown: Cleaning up resources...")
    # Example: Close the database connection
    # await db_connection.close()

app = FastAPI(lifespan=lifespan)

@app.post("/webhook")
async def webhook(request: Request):
    await handle_webhook_payload(request)


