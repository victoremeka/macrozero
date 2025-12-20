import json
from fastapi import FastAPI, Request, Response
from github_webhook import handle_webhook_payload
# import logging


# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
app = FastAPI()

@app.post("/listen")
async def listener(request: Request):
    await handle_webhook_payload(request)

@app.get("/health")
async def health_check():
    return Response(json.dumps({"status": "ok"}))
