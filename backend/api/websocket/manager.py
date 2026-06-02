"""
WebSocket connection manager.

Manages WebSocket connections per store, broadcasts events,
and handles connection failures gracefully.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import WebSocket

from db.database import Database
from engine.models import Event

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections grouped by store_id.

    Provides:
    - connect: validate store, add connection, send initial state
    - disconnect: remove connection cleanly
    - broadcast: send event to all connections for a store
    """

    def __init__(self) -> None:
        # store_id → set of WebSocket connections
        self._connections: dict[str, set[WebSocket]] = {}

    async def connect(
        self, store_id: str, ws: WebSocket, db: Database | None
    ) -> bool:
        """Accept and register a WebSocket connection.

        Validates store_id exists in DB. Rejects with close code 4004 if not.
        Sends last 50 events as initial_state payload on success.

        Args:
            store_id: The store to subscribe to.
            ws: The WebSocket connection.
            db: Database instance for validation and initial state.

        Returns:
            True if connected successfully, False if rejected.
        """
        # Validate store exists
        if db is not None:
            row = await db.fetchone(
                "SELECT store_id FROM stores WHERE store_id = ?", (store_id,)
            )
            if row is None:
                await ws.accept()
                await ws.send_json({"type": "error", "code": 4004, "reason": "Store not found"})
                return False

        await ws.accept()

        # Add to connections
        if store_id not in self._connections:
            self._connections[store_id] = set()
        self._connections[store_id].add(ws)

        # Send initial state (last 50 events)
        if db is not None:
            try:
                rows = await db.fetchall(
                    """
                    SELECT event_id, event_type, store_id, visitor_id,
                           timestamp, camera_id, attributes_json
                    FROM events
                    WHERE store_id = ?
                    ORDER BY timestamp DESC
                    LIMIT 50
                    """,
                    (store_id,),
                )
                events_list = []
                for r in rows:
                    attrs = {}
                    try:
                        attrs = json.loads(r[6]) if r[6] else {}
                    except (json.JSONDecodeError, TypeError):
                        pass
                    events_list.append({
                        "event_id": r[0],
                        "event_type": r[1],
                        "store_id": r[2],
                        "visitor_id": r[3],
                        "timestamp": r[4],
                        "camera_id": r[5],
                        "attributes": attrs,
                    })

                await ws.send_json({
                    "type": "initial_state",
                    "events": events_list,
                })
            except Exception as exc:
                logger.warning(
                    "Failed to send initial state to %s: %s", store_id, exc
                )

        logger.debug("WebSocket connected: store=%s", store_id)
        return True

    def disconnect(self, store_id: str, ws: WebSocket) -> None:
        """Remove a WebSocket connection from the pool.

        No effect on other connections.

        Args:
            store_id: The store the connection was subscribed to.
            ws: The WebSocket connection to remove.
        """
        if store_id in self._connections:
            self._connections[store_id].discard(ws)
            if not self._connections[store_id]:
                del self._connections[store_id]
        logger.debug("WebSocket disconnected: store=%s", store_id)

    async def broadcast(self, event: Event) -> None:
        """Broadcast an event to all connections for its store.

        On send error: close that connection with code 1011 and log.
        Does not affect other connections.

        Args:
            event: The Event to broadcast.
        """
        store_id = event.store_id
        connections = self._connections.get(store_id)
        if not connections:
            return

        payload = json.dumps({
            "type": "event",
            "data": event.to_dict(),
        })

        # Iterate over a copy to allow removal during iteration
        failed: list[WebSocket] = []
        for ws in list(connections):
            try:
                await ws.send_text(payload)
            except Exception as exc:
                logger.warning(
                    "WebSocket send failed for store=%s: %s", store_id, exc
                )
                failed.append(ws)

        # Close failed connections
        for ws in failed:
            connections.discard(ws)
            try:
                await ws.close(code=1011)
            except Exception:
                pass

        if not connections:
            del self._connections[store_id]

    def get_connection_count(self, store_id: str) -> int:
        """Return number of active connections for a store."""
        return len(self._connections.get(store_id, set()))

    def get_total_connections(self) -> int:
        """Return total number of active connections across all stores."""
        return sum(len(s) for s in self._connections.values())
