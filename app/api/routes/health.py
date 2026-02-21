from fastapi import APIRouter
from app.db.mongo import get_db

router = APIRouter()

# ✅ Importante: NO usar "/" aquí porque eso es de la WEB.
@router.get("/api")
async def api_root():
    return {"name": "Chronos API", "status": "ok"}

@router.get("/health")
async def health():
    db = get_db()
    await db.command("ping")
    return {"ok": True}
