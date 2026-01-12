from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from app.websocket.manager import ConnectionManager
import asyncio
import datetime

app = FastAPI()
manager = ConnectionManager()


@app.get("/")
def health_check():
    return {"status": "ok", "service": "signal-backend"}


@app.websocket("/ws/signals")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ---- MOCK DE SEÑALES (TEMPORAL) ----
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
