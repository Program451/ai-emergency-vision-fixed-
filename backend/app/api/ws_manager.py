

import asyncio
import json

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self._loop: asyncio.AbstractEventLoop | None = None

    def set_loop(self, loop: asyncio.AbstractEventLoop):
        """Вызывается один раз при старте FastAPI (main.py, on_startup)."""
        self._loop = loop

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def _broadcast_async(self, data: dict):
        message = json.dumps(data, default=str)
        dead = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                dead.append(connection)
        for d in dead:
            self.disconnect(d)

    def broadcast_threadsafe(self, data: dict):
        """Вызывать из worker-потока (НЕ из asyncio-кода)."""
        if self._loop is None:
            return
        asyncio.run_coroutine_threadsafe(self._broadcast_async(data), self._loop)


# Синглтон на весь процесс — импортируется и в api/websocket.py, и в pipeline_runner.py
manager = ConnectionManager()
