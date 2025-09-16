import os
from fastapi import APIRouter, HTTPException, status, Cookie, Response
from fastapi.responses import RedirectResponse
from typing import Optional

from pydantic import BaseModel
import requests
from utils.jwt_manager import create_access_token, verify_token
from utils.state_store import oauth_state_store

# GitHub OAuth Configuration
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")

if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
    raise ValueError(
        "GitHub OAuth credentials not configured. Set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET environment variables."
    )

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.get("/login")
async def github_login():
    """Redirect to GitHub OAuth"""
    state = oauth_state_store.generate_state()
    github_auth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={GITHUB_CLIENT_ID}"
        f"&scope=user:email"
        f"&state={state}"
    )
    return {"url": github_auth_url, "state": state}


class CallbackInfo(BaseModel):
    code: str
    state: str


@router.post("/callback")
async def github_callback(callback_info: CallbackInfo, response: Response):
    """Handle GitHub OAuth callback"""
    code = callback_info.code
    state = callback_info.state

    if not code:
        raise HTTPException(status_code=400, detail="Authorization code not provided")

    if not state:
        raise HTTPException(status_code=400, detail="State parameter missing")

    # Validate state to prevent CSRF attacks
    if not oauth_state_store.validate_state(state):
        raise HTTPException(status_code=400, detail="Invalid or expired state")

    token_response = requests.post(
        "https://github.com/login/oauth/access_token",
        data={
            "client_id": GITHUB_CLIENT_ID,
            "client_secret": GITHUB_CLIENT_SECRET,
            "code": code,
        },
        headers={"Accept": "application/json"},
    )

    if token_response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to exchange code for token")

    token_data = token_response.json()
    access_token = token_data.get("access_token")

    if not access_token:
        raise HTTPException(status_code=400, detail="No access token received")

    # Get user info from GitHub
    user_response = requests.get(
        "https://api.github.com/user",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    if user_response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to get user info")

    user_data = user_response.json()

    # Get user email (GitHub may not return email in user endpoint)
    email_response = requests.get(
        "https://api.github.com/user/emails",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    emails = []
    if email_response.status_code == 200:
        email_data = email_response.json()
        primary_email = next(
            (email["email"] for email in email_data if email["primary"]), None
        )
        emails = [email["email"] for email in email_data]

    # Create JWT with user data
    jwt_payload = {
        "github_id": user_data["id"],
        "username": user_data["login"],
        "name": user_data.get("name"),
        "email": (
            primary_email if "primary_email" in locals() else user_data.get("email")
        ),
        "avatar_url": user_data.get("avatar_url"),
        "emails": emails,
    }

    jwt_token = create_access_token(jwt_payload)

    # Set JWT as HTTP-only cookie
    response.set_cookie(
        key="access_token",
        value=jwt_token,
        httponly=True,
        secure=os.getenv("ENVIRONMENT", "development").lower() == "production",
        samesite="lax",
        max_age=24 * 60 * 60,  # 24 hours
        path="/",
    )

    return {
        "message": "Login successful",
    }


@router.get("/me")
async def get_current_user(access_token: Optional[str] = Cookie(None)):
    """Get current user info from JWT"""
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )

    user_data = verify_token(access_token)
    # Remove exp from response
    user_data.pop("exp", None)
    return user_data


@router.post("/logout")
async def logout(response: Response):
    """Logout user by clearing the cookie"""
    response.delete_cookie(
        key="access_token",
        path="/",
        samesite="lax",
    )
    return {"message": "Successfully logged out"}
