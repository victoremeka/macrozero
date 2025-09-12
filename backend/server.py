from fastapi import FastAPI, Request, Depends
from contextlib import asynccontextmanager
from db import create_db_and_tables
from apis.github_webhook import handle_webhook_payload
from routers.auth import router as auth_router
from middleware.auth import require_auth, optional_auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield
    print("Application shutdown: Cleaning up resources...")
    # Example: Close the database connection
    # await db_connection.close()


app = FastAPI(lifespan=lifespan)

# Include routers
app.include_router(auth_router)


@app.post("/webhook")
async def webhook(request: Request):
    await handle_webhook_payload(request)


# Example protected route
@app.get("/protected")
async def protected_route(current_user: dict = Depends(require_auth)):
    return {"message": "This is a protected route", "user": current_user}


# Example optional auth route
@app.get("/")
async def root(current_user: dict = Depends(optional_auth)):
    if current_user:
        return {"message": f"Hello {current_user.get('username', 'User')}!"}
    return {"message": "Hello Guest!"}
