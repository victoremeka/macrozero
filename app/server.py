from fastapi import FastAPI, Request
from app.github_webhook import handle_webhook_payload

app = FastAPI()

@app.post("/listen")
async def listener(request: Request):
    await handle_webhook_payload(request)
