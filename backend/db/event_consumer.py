"""
Event consumer: persists events from event_queue to SQLite.

Consumes Event objects from the event_queue, writes them to the database,
and broadcasts to WebSocket clients (when ws_manager is available).

Retry policy: on DB failure, retry 3x with exponential backoff (1s, 2s, 4s).
Logs full payload on final failure.
"""

from __future__ import annotations

import asyncio
import json
import logging

from db.database import Database
from engine.models import Event

logger = logging.getLogger(__name__)

# Retry configuration
MAX_RETRIES = 3
BACKOFF_BASE_SECONDS = 1.0


async def event_consumer(
    event_queue: asyncio.Queue,
    db: Database | None,
    ws_manager=None,
) -> None:
    """Consume events from event_queue, persist to DB, broadcast to WS.

    Args:
        event_queue: Queue of Event objects from EventEngine.
        db: Database instance (may be None if DB not yet available).
        ws_manager: WebSocket ConnectionManager (None until Phase 8).
    """
    logger.info("event_consumer started")

    try:
        while True:
            event: Event = await event_queue.get()

            # Persist to database
            if db is not None:
                await _persist_with_retry(db, event)

            # Broadcast to WebSocket clients
            if ws_manager is not None:
                try:
                    await ws_manager.broadcast(event)
                except Exception as exc:
                    logger.warning(
                        "WebSocket broadcast failed for event %s: %s",
                        event.event_id,
                        exc,
                    )

            event_queue.task_done()

    except asyncio.CancelledError:
        logger.info("event_consumer cancelled")
        raise


async def _persist_with_retry(db: Database, event: Event) -> None:
    """Persist an event with retry on failure.

    Retries 3x with exponential backoff: 1s, 2s, 4s.
    Logs full payload on final failure.
    """
    for attempt in range(MAX_RETRIES):
        try:
            await db.upsert_event(event)
            return
        except Exception as exc:
            backoff = BACKOFF_BASE_SECONDS * (2 ** attempt)
            if attempt < MAX_RETRIES - 1:
                logger.warning(
                    "DB write failed (attempt %d/%d) for event %s: %s. "
                    "Retrying in %.1fs...",
                    attempt + 1,
                    MAX_RETRIES,
                    event.event_id,
                    exc,
                    backoff,
                )
                await asyncio.sleep(backoff)
            else:
                logger.error(
                    "DB write FAILED after %d attempts for event %s. "
                    "Payload: %s",
                    MAX_RETRIES,
                    event.event_id,
                    json.dumps(event.to_dict()),
                )
