from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.db.mongo import get_db

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")

PORTADA WEB (ahora sí es una web real)

@router.get("/", response_class=HTMLResponse)
async def root(request: Request):
return templates.TemplateResponse(
"index.html",
{"request": request}
)

HEALTHCHECK PARA RAILWAY

@router.get("/health")
async def health():
db = get_db()
await db.command("ping")
return {"ok": True}
