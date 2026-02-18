from fastapi import APIRouter
from app.db.mongo import get_db

router = APIRouter()

@router.get("/")
async def root():
    return {"name": "Chronos API", "status": "ok"}

@router.get("/health")
async def health():
    db = get_db()
    await db.command("ping")
    return {"ok": True}
