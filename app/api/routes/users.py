from fastapi import APIRouter, Depends
from app.deps.auth import get_current_user

router = APIRouter()

@router.get("/me")
async def me(user = Depends(get_current_user)):
    # convertir _id a string para que Pydantic no falle
    if user.get("_id") is not None:
        user["_id"] = str(user["_id"])
    return user
