from fastapi import APIRouter, Depends
from app.core.auth import get_current_user
from app.services.referral_service import get_or_create_referral_code

router = APIRouter(prefix="/referral", tags=["referral"])


@router.get("/my-code")
async def my_code(user=Depends(get_current_user)):
    code = await get_or_create_referral_code(user)
    return {"code": code}
