from typing import Set, Optional
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.dashboards: Set[WebSocket] = set()
        self.bot: Optional[WebSocket] = None

    async def connect_dashboard(self, websocket: WebSocket):
        await websocket.accept()
        self.dashboards.add(websocket)

    def disconnect_dashboard(self, websocket: WebSocket):
        if websocket in self.dashboards:
            self.dashboards.remove(websocket)

    async def connect_bot(self, websocket: WebSocket):
        await websocket.accept()
        self.bot = websocket

    def disconnect_bot(self):
        self.bot = None

    async def broadcast_to_dashboards(self, message: dict):
        dead_sockets = set()
        for connection in self.dashboards:
            try:
                await connection.send_json(message)
            except Exception:
                dead_sockets.add(connection)
        for dead in dead_sockets:
            if dead in self.dashboards:
                self.dashboards.remove(dead)

    async def send_to_bot(self, message: dict):
        if self.bot:
            try:
                await self.bot.send_json(message)
            except Exception:
                self.bot = None

manager = ConnectionManager()
