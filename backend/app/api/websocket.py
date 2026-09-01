from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.api.ws_manager import manager

router = APIRouter()


@router.websocket("/ws/incidents")
async def incidents_socket(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Dashboard ничего не шлёт — просто держим соединение открытым
            # и ждём, пока сервер сам не broadcast'нет обновление.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
