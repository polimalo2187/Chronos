from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
import asyncio
import datetime
from app.websocket.manager import ConnectionManager

app = FastAPI()
manager = ConnectionManager()

# Carpeta de templates y static
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Página principal
@app.get("/", response_class=HTMLResponse)
async def get_dashboard(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# WebSocket
@app.websocket("/ws/signals")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# ---- Mock de señales ----
async def mock_signal_emitter():
    while True:
        signal = {
            "pair": "BTCUSDT",
            "signal": "LONG",
            "price": 42350,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }
        await manager.broadcast(signal)
        await asyncio.sleep(5)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(mock_signal_emitter())
