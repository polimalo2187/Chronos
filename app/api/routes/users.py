from fastapi import APIRouter, Depends
from app.deps.auth import get_current_user
from app.schemas.user import UserOut

router = APIRouter()

@router.get("/me", response_model=UserOut)
async def me(user = Depends(get_current_user)):
    user["_id"] = str(user["_id"])
    # seguridad: nunca devolver hash
    user.pop("password_hash", None)
    return user
