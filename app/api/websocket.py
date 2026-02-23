"""WebSocket endpoint for real-time updates."""

import asyncio
import json
from typing import Dict, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.security import get_current_user_ws

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections."""

    def __init__(self):
        # Store active connections: user_id -> set of websockets
        self.active_connections: Dict[int, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)

    def disconnect(self, websocket: WebSocket, user_id: int):
        """Remove a WebSocket connection."""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_personal_message(self, message: dict, user_id: int):
        """Send a message to all connections of a specific user."""
        if user_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.add(connection)

            # Clean up disconnected connections
            for conn in disconnected:
                self.disconnect(conn, user_id)

    async def broadcast_to_user(self, user_id: int, event_type: str, data: dict):
        """Broadcast an event to all user's connections."""
        message = {"type": event_type, "data": data, "timestamp": asyncio.get_event_loop().time()}
        await self.send_personal_message(message, user_id)


# Global connection manager instance
manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = None,
):
    """
    WebSocket endpoint for real-time updates.

    Connect with: ws://localhost:8000/ws?token=YOUR_JWT_TOKEN

    Events sent to client:
    - document_processing_started
    - document_processing_progress
    - document_processing_completed
    - document_processing_failed
    - transaction_created
    - transaction_updated
    - transaction_deleted
    """
    if not token:
        await websocket.close(code=4001, reason="Missing authentication token")
        return

    try:
        # Authenticate user
        user = await get_current_user_ws(token)
        user_id = user.id

        # Connect
        await manager.connect(websocket, user_id)

        # Send connection confirmation
        await websocket.send_json(
            {"type": "connection_established", "data": {"user_id": user_id, "email": user.email}}
        )

        # Keep connection alive and handle incoming messages
        try:
            while True:
                # Receive messages (for ping/pong or client requests)
                data = await websocket.receive_text()
                message = json.loads(data)

                # Handle ping
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})

        except WebSocketDisconnect:
            manager.disconnect(websocket, user_id)

    except Exception as e:
        await websocket.close(code=4003, reason=f"Authentication failed: {str(e)}")


async def notify_document_processing(
    user_id: int, document_id: int, status: str, progress: int = None, error: str = None
):
    """Notify user about document processing status."""
    data = {
        "document_id": document_id,
        "status": status,
    }

    if progress is not None:
        data["progress"] = progress

    if error:
        data["error"] = error

    event_type = f"document_processing_{status}"
    await manager.broadcast_to_user(user_id, event_type, data)


async def notify_transaction_event(user_id: int, event: str, transaction_data: dict):
    """Notify user about transaction events."""
    await manager.broadcast_to_user(user_id, f"transaction_{event}", transaction_data)
