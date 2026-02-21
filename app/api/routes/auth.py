from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.services.users import create_user, authenticate_user
from app.deps.auth import get_current_user
from app.core.security import create_access_token

router = APIRouter()

class AuthRequest(BaseModel):
    email: str
    password: str

@router.post("/register")
async def register(payload: AuthRequest):
    user = await create_user(payload.email, payload.password)
    return {"ok": True, "user_id": str(user["_id"])}

@router.post("/login")
async def login(payload: AuthRequest):
    user = await authenticate_user(payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": user["email"]})
    return {"access_token": token, "token_type": "bearer"}

@router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    # devolver campos seguros (no password hash)
    return {
        "id": str(user.get("_id")),
        "email": user.get("email"),
        "plan": user.get("plan", "free"),
        "plan_expires_at": user.get("plan_expires_at"),
        "status": user.get("status", "active"),
        "is_admin": bool(user.get("is_admin", False)),
        "telegram_id": user.get("telegram_id"),
    }
