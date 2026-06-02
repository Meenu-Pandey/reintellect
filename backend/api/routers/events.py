"""
Event ingestion endpoint.

POST /events/ingest — Accept single event or batch (up to 500).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from api.dependencies import get_db
from db.database import Database
from engine.models import EVENT_TYPES, Event

router = APIRouter()

MAX_BATCH_SIZE = 500


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class EventInput(BaseModel):
    event_id: str
    event_type: str
    store_id: str
    visitor_id: str
    timestamp: str  # ISO 8601
    camera_id: str
    attributes: dict[str, Any] = {}


class EventIngestBody(BaseModel):
    """Accepts either a single event or a list of events."""
    # We handle polymorphic input in the endpoint directly
    pass


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def _validate_event(event: dict, index: int | None = None) -> list[str]:
    """Validate a single event dict. Returns list of error messages."""
    errors = []
    prefix = f"event[{index}]" if index is not None else "event"

    # Required fields
    required = {"event_id", "event_type", "store_id", "visitor_id", "timestamp", "camera_id"}
    missing = required - set(event.keys())
    if missing:
        errors.append(f"{prefix}: missing required fields: {sorted(missing)}")
        return errors

    # event_type validation
    if event["event_type"] not in EVENT_TYPES:
        errors.append(
            f"{prefix}: event_type must be one of {sorted(EVENT_TYPES)}, "
            f"got '{event['event_type']}'"
        )

    # timestamp validation
    try:
        ts_str = event["timestamp"].replace("Z", "+00:00")
        datetime.fromisoformat(ts_str)
    except (ValueError, TypeError, AttributeError):
        errors.append(f"{prefix}: invalid timestamp format")

    # event_id must be non-empty string
    if not event.get("event_id"):
        errors.append(f"{prefix}: event_id must be a non-empty string")

    # visitor_id must be non-empty string
    if not event.get("visitor_id"):
        errors.append(f"{prefix}: visitor_id must be a non-empty string")

    # store_id must be non-empty string
    if not event.get("store_id"):
        errors.append(f"{prefix}: store_id must be a non-empty string")

    # camera_id must be non-empty string
    if not event.get("camera_id"):
        errors.append(f"{prefix}: camera_id must be a non-empty string")

    return errors


def _parse_event(event_dict: dict) -> Event:
    """Parse a validated event dict into an Event object."""
    ts_str = event_dict["timestamp"].replace("Z", "+00:00")
    ts = datetime.fromisoformat(ts_str)
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)

    return Event(
        event_id=event_dict["event_id"],
        event_type=event_dict["event_type"],
        store_id=event_dict["store_id"],
        visitor_id=event_dict["visitor_id"],
        timestamp=ts,
        camera_id=event_dict["camera_id"],
        attributes=event_dict.get("attributes", {}),
    )


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.post("/events/ingest")
async def ingest_events(
    request: Request,
    db: Database | None = Depends(get_db),
) -> JSONResponse:
    """Ingest single event or batch of up to 500 events.

    Single event:
    - Valid and new → 201
    - Duplicate event_id → 200 with original
    - Invalid → 422

    Batch:
    - All valid → upsert all, return 201 (all new) or 200 (some existed)
    - Any invalid → 422 with per-index errors, nothing written
    """
    if db is None:
        return JSONResponse(
            status_code=503,
            content={"detail": "Database unavailable"},
        )

    body = await request.json()

    # Determine if single or batch
    if isinstance(body, list):
        return await _handle_batch(body, db)
    elif isinstance(body, dict):
        return await _handle_single(body, db)
    else:
        return JSONResponse(
            status_code=422,
            content={"detail": "Body must be an event object or array of events"},
        )


async def _handle_single(event_dict: dict, db: Database) -> JSONResponse:
    """Handle single event ingestion."""
    # Validate
    errors = _validate_event(event_dict)
    if errors:
        return JSONResponse(status_code=422, content={"detail": errors})

    # Check if duplicate
    existing = await db.fetchone(
        "SELECT event_id, event_type, store_id, visitor_id, timestamp, camera_id, attributes_json FROM events WHERE event_id = ?",
        (event_dict["event_id"],),
    )
    if existing:
        # Return 200 with original
        return JSONResponse(
            status_code=200,
            content={
                "event_id": existing[0],
                "event_type": existing[1],
                "store_id": existing[2],
                "visitor_id": existing[3],
                "timestamp": existing[4],
                "camera_id": existing[5],
                "attributes": _safe_json_loads(existing[6]),
                "duplicate": True,
            },
        )

    # Parse and persist
    event = _parse_event(event_dict)
    await db.upsert_event(event)

    return JSONResponse(
        status_code=201,
        content={
            "event_id": event.event_id,
            "event_type": event.event_type,
            "store_id": event.store_id,
            "visitor_id": event.visitor_id,
            "timestamp": event.timestamp.isoformat(),
            "camera_id": event.camera_id,
            "attributes": event.attributes,
            "duplicate": False,
        },
    )


async def _handle_batch(events_list: list, db: Database) -> JSONResponse:
    """Handle batch event ingestion (up to 500, atomic rejection)."""
    if len(events_list) > MAX_BATCH_SIZE:
        return JSONResponse(
            status_code=422,
            content={"detail": f"Batch size exceeds maximum of {MAX_BATCH_SIZE}"},
        )

    if len(events_list) == 0:
        return JSONResponse(
            status_code=422,
            content={"detail": "Batch must contain at least 1 event"},
        )

    # Validate ALL events first
    all_errors: list[dict] = []
    for i, event_dict in enumerate(events_list):
        if not isinstance(event_dict, dict):
            all_errors.append({"index": i, "errors": [f"event[{i}]: must be an object"]})
            continue
        errors = _validate_event(event_dict, index=i)
        if errors:
            all_errors.append({"index": i, "errors": errors})

    # If any fail, reject entire batch atomically
    if all_errors:
        return JSONResponse(
            status_code=422,
            content={"detail": "Batch validation failed", "errors": all_errors},
        )

    # All valid — upsert all
    new_count = 0
    existing_count = 0
    for event_dict in events_list:
        # Check duplicate
        existing = await db.fetchone(
            "SELECT event_id FROM events WHERE event_id = ?",
            (event_dict["event_id"],),
        )
        if existing:
            existing_count += 1
        else:
            new_count += 1

        event = _parse_event(event_dict)
        await db.upsert_event(event)

    status_code = 201 if existing_count == 0 else 200
    return JSONResponse(
        status_code=status_code,
        content={
            "ingested": len(events_list),
            "new": new_count,
            "duplicates": existing_count,
        },
    )


def _safe_json_loads(s: str | None) -> dict:
    """Safely parse JSON string, returning empty dict on failure."""
    if not s:
        return {}
    try:
        import json
        return json.loads(s)
    except (json.JSONDecodeError, TypeError):
        return {}
