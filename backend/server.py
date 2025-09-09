from fastapi import FastAPI, Request
from apis.github_webhook import *

app = FastAPI()

@app.post("/webhook")
async def webhook(request: Request):
    await handle_webhook_pull_request(request)

