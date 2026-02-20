from fastapi import APIRouter, Depends
from app.deps.auth import get_current_user

router = APIRouter()


@router.get("/me")
async def me(user=Depends(get_current_user)):
    # convertir ObjectId a string
    user["_id"] = str(user["_id"])

    # seguridad: nunca devolver hash
    user.pop("password_hash", None)

    return user
