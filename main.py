# main.py
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import os

# Crear la app FastAPI
app = FastAPI()

# Montar carpeta static para imágenes, CSS, JS
static_path = os.path.join(os.path.dirname(__file__), "app", "static")
app.mount("/static", StaticFiles(directory=static_path), name="static")

# Configurar templates (HTML)
templates_path = os.path.join(os.path.dirname(__file__), "app", "templates")
templates = Jinja2Templates(directory=templates_path)

# Ruta principal (dashboard)
@app.get("/", response_class=HTMLResponse)
async def read_dashboard(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Solo para correr localmente
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
