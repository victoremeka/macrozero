from fastapi import FastAPI, Request
from .apis.github import *

dotenv.load_dotenv()

app = FastAPI()



@app.post("/webhook")
async def webhook(request: Request):
    await handle_pull_request(request)
