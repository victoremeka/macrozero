from fastapi import FastAPI, Request

app = FastAPI()


@app.post("/listen")
def listener(request: Request):
    pass
