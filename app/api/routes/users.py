from fastapi import APIRouter, Depends
from app.deps.auth import get_current_user
from app.schemas.user import UserOut

router = APIRouter()

@router.get("/me", response_model=UserOut)
async def me(user: dict = Depends(get_current_user)):
    user.pop("password_hash", None)
    return user
