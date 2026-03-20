import json
from datetime import date, datetime
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
from app.utils.logger import logger
from uuid import UUID


def _json_safe(value):
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    return value

class ConnectionManager:
    def __init__(self):
        # ward -> set of websocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, ward: str = "all"):
        await websocket.accept()
        if ward not in self.active_connections:
            self.active_connections[ward] = set()
        self.active_connections[ward].add(websocket)
        logger.info(f"WebSocket connected: ward={ward}, total={self.total_connections()}")

    def disconnect(self, websocket: WebSocket, ward: str = "all"):
        if ward in self.active_connections:
            self.active_connections[ward].discard(websocket)
        logger.info(f"WebSocket disconnected: ward={ward}")

    def total_connections(self) -> int:
        return sum(len(s) for s in self.active_connections.values())

    async def send_to_ward(self, ward: str, message: dict):
        """Broadcast to all connections in a ward."""
        payload = json.dumps(_json_safe(message))
        failed = set()
        for ws in self.active_connections.get(ward, set()):
            try:
                await ws.send_text(payload)
            except Exception:
                failed.add(ws)
        self.active_connections[ward] -= failed

    async def broadcast(self, message: dict):
        """Broadcast to ALL connected clients across all wards."""
        for ward in list(self.active_connections.keys()):
            await self.send_to_ward(ward, message)

manager = ConnectionManager()


async def broadcast_event(message: dict):
    await manager.broadcast(message)

async def alert_websocket_endpoint(websocket: WebSocket, ward: str = "all"):
    await manager.connect(websocket, ward)
    try:
        # Send welcome ping
        await websocket.send_json({"type": "connected", "ward": ward, "message": "SepsisShield AI WebSocket connected"})
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            if msg.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(websocket, ward)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, ward)
