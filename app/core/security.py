from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.supabase_client import auth_client, user_client

security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        user = auth_client.auth.get_user(token)
        return user.user
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def get_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    return credentials.credentials


def get_db(token: str = Depends(get_token)):
    """A fresh database client acting as the logged-in user (one per request)."""
    return user_client(token)
