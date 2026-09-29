from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.security import get_current_user
from app.core.supabase_client import supabase

router = APIRouter()


class AuthRequest(BaseModel):
    email: str
    password: str


@router.post("/signup")
def signup(payload: AuthRequest):
    result = supabase.auth.sign_up(
        {"email": payload.email, "password": payload.password}
    )
    if result.user is None:
        raise HTTPException(status_code=400, detail="Signup failed")
    return {"user_id": result.user.id, "email": result.user.email}


@router.post("/login")
def login(payload: AuthRequest):
    result = supabase.auth.sign_in_with_password(
        {"email": payload.email, "password": payload.password}
    )
    if result.session is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"access_token": result.session.access_token, "user_id": result.user.id}


@router.get("/me")
def read_current_user(user=Depends(get_current_user)):
    return {"id": user.id, "email": user.email}
