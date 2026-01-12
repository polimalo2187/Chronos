# main.py
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

# Crear la app FastAPI
app = FastAPI()

# Montar la carpeta static para servir imágenes, CSS, JS
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Configurar templates (HTML)
templates = Jinja2Templates(directory="app/templates")

# Ruta principal (dashboard)
@app.get("/", response_class=HTMLResponse)
async def read_dashboard(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Esto solo se usa si corres localmente
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
