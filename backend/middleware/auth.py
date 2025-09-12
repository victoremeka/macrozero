from fastapi import HTTPException, status, Cookie
from typing import Optional, Dict, Any
from utils.jwt_manager import verify_token


async def get_current_user(
    access_token: Optional[str] = Cookie(None),
) -> Optional[Dict[str, Any]]:
    """
    Get current user data from JWT token.
    Returns user data if token is valid, raises unauthorized error if not authenticated.
    """
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated" 
        )

    try:
        user_data = verify_token(access_token)
        # Remove expiration from user data for cleaner response
        user_data.pop("exp", None)
        return user_data
    except HTTPException:
        return None
