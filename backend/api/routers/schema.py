"""
Event schema endpoint.

Returns the canonical JSON Schema for ReIntellect events.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()

# Canonical event JSON schema
EVENT_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "ReIntellect Event",
    "description": "Canonical event schema for the ReIntellect event stream.",
    "type": "object",
    "required": [
        "event_id",
        "event_type",
        "store_id",
        "visitor_id",
        "timestamp",
        "camera_id",
    ],
    "properties": {
        "event_id": {
            "type": "string",
            "format": "uuid",
            "description": "Client-supplied UUID v4 (idempotency key).",
        },
        "event_type": {
            "type": "string",
            "enum": [
                "ENTRY",
                "EXIT",
                "ZONE_ENTER",
                "ZONE_EXIT",
                "ZONE_DWELL",
                "BILLING_QUEUE_JOIN",
                "BILLING_QUEUE_ABANDON",
                "REENTRY",
            ],
            "description": "One of the 8 valid event types.",
        },
        "store_id": {
            "type": "string",
            "description": "Identifier of the store.",
        },
        "visitor_id": {
            "type": "string",
            "format": "uuid",
            "description": "Stable business-level visitor identifier.",
        },
        "timestamp": {
            "type": "string",
            "format": "date-time",
            "description": "UTC ISO 8601 timestamp of the event.",
        },
        "camera_id": {
            "type": "string",
            "description": "Identifier of the camera that observed the event.",
        },
        "attributes": {
            "type": "object",
            "description": "Event-type-specific fields.",
            "properties": {
                "zone_id": {"type": "string"},
                "dwell_seconds": {"type": "number", "minimum": 0},
                "queue_position": {"type": "integer", "minimum": 1},
                "wait_seconds": {"type": "number", "minimum": 0},
                "gap_seconds": {"type": "number", "minimum": 0},
                "duration_seconds": {"type": "number", "minimum": 0},
            },
            "additionalProperties": True,
        },
    },
    "additionalProperties": False,
}


@router.get("/schema/events")
async def get_event_schema() -> JSONResponse:
    """Return the canonical event JSON Schema.

    Content-Type: application/schema+json
    """
    return JSONResponse(
        content=EVENT_SCHEMA,
        media_type="application/schema+json",
    )
