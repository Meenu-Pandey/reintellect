"""
WebSocket router.

Endpoint: WS /ws/stores/{store_id}/events
- Validates store exists (4004 on unknown store)
- Sends initial_state on connect
- 60s idle timeout (close with 1001)
"""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from api.websocket.manager import ConnectionManager
from db.database import Database

logger = logging.getLogger(__name__)

router = APIRouter()

# Idle timeout in seconds
IDLE_TIMEOUT_SECONDS = 60


@router.websocket("/ws/stores/{store_id}/events")
async def websocket_events(websocket: WebSocket, store_id: str) -> None:
    """WebSocket endpoint for real-time event streaming.

    Validates store, sends initial state, then keeps connection alive.
    Closes with 4004 for unknown stores.
    Closes with 1001 after 60s of idle (no ping from client).
    """
    # Get manager and db from app state
    app = websocket.app
    ws_manager: ConnectionManager | None = getattr(app.state, "ws_manager", None)
    db: Database | None = getattr(app.state, "db", None)

    if ws_manager is None:
        await websocket.close(code=1011)
        return

    # Connect (validates store, sends initial state)
    connected = await ws_manager.connect(store_id, websocket, db)
    if not connected:
        # Store not found — manager already sent error JSON, close with 4004
        await websocket.close(code=4004)
        return

    try:
        # Receive loop with idle timeout
        while True:
            try:
                # Wait for client message (ping/pong or data) with timeout
                await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=IDLE_TIMEOUT_SECONDS,
                )
            except asyncio.TimeoutError:
                # Idle timeout — close connection
                logger.info(
                    "WebSocket idle timeout for store=%s, closing with 1001",
                    store_id,
                )
                await websocket.close(code=1001)
                break
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.warning("WebSocket error for store=%s: %s", store_id, exc)
    finally:
        ws_manager.disconnect(store_id, websocket)
