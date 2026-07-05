from typing import Set, Optional
from fastapi import WebSocket

class ConnectionManager:
    """
    Manages active WebSocket connections for the Penalty Game monorepo.
    Bridges communication between:
      1. Dashboard Frontends (Next.js clients)
      2. Automation Bot Client (Playwright automation loop)
    """
    def __init__(self):
        # Store active frontend dashboard WebSocket connections
        self.dashboards: Set[WebSocket] = set()
        # Track the active automation bot client connection
        self.bot: Optional[WebSocket] = None

    async def connect_dashboard(self, websocket: WebSocket):
        """
        Accepts and registers a new Next.js dashboard client connection.
        """
        await websocket.accept()
        self.dashboards.add(websocket)
        print(f"[WS Manager] Dashboard client connected. Total clients: {len(self.dashboards)}")

    def disconnect_dashboard(self, websocket: WebSocket):
        """
        Removes a dashboard client from the registry upon disconnect.
        """
        if websocket in self.dashboards:
            self.dashboards.remove(websocket)
            print(f"[WS Manager] Dashboard client disconnected. Remaining: {len(self.dashboards)}")

    async def connect_bot(self, websocket: WebSocket):
        """
        Accepts and registers the automation script as the active bot controller.
        """
        await websocket.accept()
        self.bot = websocket
        print("[WS Manager] Automation bot client connected.")

    def disconnect_bot(self):
        """
        Unregisters the bot controller upon disconnect.
        """
        self.bot = None
        print("[WS Manager] Automation bot client disconnected.")

    async def broadcast_to_dashboards(self, message: dict):
        """
        Broadcasts telemetry, updates, and logs to all connected dashboards.
        Cleans up stale or dead WebSocket sockets.
        """
        dead_sockets = set()
        for connection in self.dashboards:
            try:
                await connection.send_json(message)
            except Exception:
                dead_sockets.add(connection)
                
        # Clean up any dead connections encountered
        for dead in dead_sockets:
            if dead in self.dashboards:
                self.dashboards.remove(dead)

    async def send_to_bot(self, message: dict):
        """
        Relays instruction packets (e.g. START/STOP commands) from dashboards
        directly to the active bot controller.
        """
        if self.bot:
            try:
                await self.bot.send_json(message)
            except Exception as e:
                print(f"[WS Manager] Error sending message to bot: {e}")
                self.bot = None  # Clear bot connection if it has died

# Singleton instance of the connection manager
manager = ConnectionManager()
