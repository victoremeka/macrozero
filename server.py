from fastapi import FastAPI, Request
from github_webhook import handle_webhook_payload
# import logging


# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
app = FastAPI()

@app.post("/listen")
async def listener(request: Request):
    await handle_webhook_payload(request)
