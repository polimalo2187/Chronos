from fastapi import APIRouter
from app.db.mongo import get_db

router = APIRouter()

@router.get("/api")
async def api_root():
    return {"name": "Chronos API", "status": "ok"}

@router.get("/health")
async def health():
    db = get_db()
    await db.command("ping")
    return {"ok": True}

@router.get("/api/whatsapp")
async def whatsapp():
    # Devuelve url si está configurado
    from app.core.config import settings
    url = (settings.whatsapp_contact or "").strip()
    return {"url": url} if url else {"url": None}
