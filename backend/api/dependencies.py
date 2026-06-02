"""
Shared FastAPI dependencies for the ReIntellect API.

Provides dependency injection for database, event queue, and WebSocket manager.
"""

from __future__ import annotations

import asyncio

from fastapi import Request

from db.database import Database


def get_db(request: Request) -> Database | None:
    """Get the singleton Database instance from app state."""
    return request.app.state.db


def get_event_queue(request: Request) -> asyncio.Queue:
    """Get the event queue from app state."""
    return request.app.state.event_queue


def get_ws_manager(request: Request):
    """Get the WebSocket ConnectionManager from app state.

    Returns None until Phase 8 wires in the ConnectionManager.
    """
    return getattr(request.app.state, "ws_manager", None)
