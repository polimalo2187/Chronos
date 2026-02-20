from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.db.mongo import get_db

router = APIRouter()

# Templates folder (debe existir: app/templates/index.html)
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def root(request: Request):
    # PORTADA WEB (ahora sí es una web real)
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/health")
async def health():
    # HEALTHCHECK PARA RAILWAY
    db = get_db()
    await db.command("ping")
    return {"ok": True}
