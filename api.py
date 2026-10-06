from __future__ import annotations

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from .liars_dice import DiceHub
from .liars_dice_ui import DICE_HTML

app = FastAPI(title="Last Die Standing", version="1.0.0")
hub = DiceHub()


@app.get("/", response_class=HTMLResponse)
async def home() -> str:
    return DICE_HTML


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "game": "last-die-standing"}


@app.websocket("/ws/dice")
async def dice_socket(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        while True:
            payload = await websocket.receive_json()
            if isinstance(payload, dict):
                await hub.handle_socket_message(websocket, payload)
            else:
                await websocket.send_json(
                    {"type": "error", "code": "INVALID_ACTION", "message": "Send a structured command."}
                )
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        await hub.disconnect(websocket)
