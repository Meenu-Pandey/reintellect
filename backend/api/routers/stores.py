"""
Store layout and transaction endpoints.

POST /stores — Create/update store layout with polygon validation.
POST /stores/{store_id}/transactions — Ingest POS transactions.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from shapely.geometry import Polygon as ShapelyPolygon

from api.dependencies import get_db
from db.database import Database

router = APIRouter()


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class ZoneInput(BaseModel):
    zone_id: str
    zone_type: str
    name: str | None = None
    camera_id: str | None = None
    polygon: list[list[float]]  # List of [x, y] pairs


class CameraInput(BaseModel):
    camera_id: str
    name: str | None = None
    position: str | None = None


class StoreLayoutInput(BaseModel):
    store_id: str
    name: str
    timezone: str = "Asia/Kolkata"
    zones: list[ZoneInput]
    cameras: list[CameraInput] = Field(default_factory=list)


class TransactionInput(BaseModel):
    transaction_id: str
    timestamp: str  # ISO 8601
    amount: float
    visitor_id: str | None = None


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

ALLOWED_ZONE_TYPES = {"entry", "exit", "floor", "billing_queue", "restricted"}


def _validate_polygon(points: list[list[float]], zone_id: str) -> list[str]:
    """Validate a polygon and return list of error messages."""
    errors = []

    if len(points) < 3:
        errors.append(f"Zone '{zone_id}': polygon must have at least 3 vertices, got {len(points)}")
        return errors

    # Check all coordinates in [0.0, 1.0]
    for i, pt in enumerate(points):
        if len(pt) != 2:
            errors.append(f"Zone '{zone_id}': point {i} must have 2 coordinates")
            continue
        x, y = pt
        if not (0.0 <= x <= 1.0) or not (0.0 <= y <= 1.0):
            errors.append(
                f"Zone '{zone_id}': point {i} coordinates must be in [0.0, 1.0], got ({x}, {y})"
            )

    if errors:
        return errors

    # Check non-self-intersecting
    try:
        poly = ShapelyPolygon([(p[0], p[1]) for p in points])
        if not poly.is_valid:
            errors.append(f"Zone '{zone_id}': polygon is self-intersecting or invalid")
    except Exception as exc:
        errors.append(f"Zone '{zone_id}': invalid polygon geometry: {exc}")

    return errors


def _validate_store_layout(layout: StoreLayoutInput) -> list[str]:
    """Validate the full store layout. Returns list of error messages."""
    errors = []

    zone_ids = set()
    for zone in layout.zones:
        # Zone type validation
        if zone.zone_type not in ALLOWED_ZONE_TYPES:
            errors.append(
                f"Zone '{zone.zone_id}': zone_type must be one of {sorted(ALLOWED_ZONE_TYPES)}, "
                f"got '{zone.zone_type}'"
            )

        # Duplicate zone_id check
        if zone.zone_id in zone_ids:
            errors.append(f"Zone '{zone.zone_id}': duplicate zone_id")
        zone_ids.add(zone.zone_id)

        # Polygon validation
        poly_errors = _validate_polygon(zone.polygon, zone.zone_id)
        errors.extend(poly_errors)

    # Check camera references
    for camera in layout.cameras:
        # Cameras don't reference zone_ids directly in our schema, so no check needed
        pass

    return errors


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/stores")
async def create_store_layout(
    body: StoreLayoutInput,
    request: Request,
    db: Database | None = Depends(get_db),
) -> JSONResponse:
    """Create or update a store layout.

    Validates all polygons:
    - Minimum 3 points
    - Non-self-intersecting
    - Coordinates in [0.0, 1.0]
    - zone_type in allowed set

    Returns 200 on success, 422 on validation failure.
    """
    # Validate
    errors = _validate_store_layout(body)
    if errors:
        return JSONResponse(
            status_code=422,
            content={"detail": errors},
        )

    if db is None:
        return JSONResponse(
            status_code=503,
            content={"detail": "Database unavailable"},
        )

    # Build layout dict for database
    layout_dict: dict[str, Any] = {
        "store_id": body.store_id,
        "name": body.name,
        "timezone": body.timezone,
        "zones": [
            {
                "zone_id": z.zone_id,
                "zone_type": z.zone_type,
                "name": z.name or z.zone_id,
                "camera_id": z.camera_id,
                "polygon": [(p[0], p[1]) for p in z.polygon],
            }
            for z in body.zones
        ],
        "cameras": [
            {
                "camera_id": c.camera_id,
                "name": c.name,
                "position": c.position,
            }
            for c in body.cameras
        ],
    }

    await db.upsert_store(layout_dict)

    return JSONResponse(
        status_code=200,
        content={
            "store_id": body.store_id,
            "name": body.name,
            "timezone": body.timezone,
            "zones_count": len(body.zones),
            "cameras_count": len(body.cameras),
        },
    )


@router.post("/stores/{store_id}/transactions")
async def create_transaction(
    store_id: str,
    body: TransactionInput,
    request: Request,
    db: Database | None = Depends(get_db),
) -> JSONResponse:
    """Ingest a POS transaction.

    Validates timestamp is not > 24h in past or in future.
    Correlates to visitor if visitor_id provided, marks converted=true.
    If no visitor_id, attempts to correlate via billing queue events.
    """
    if db is None:
        return JSONResponse(
            status_code=503,
            content={"detail": "Database unavailable"},
        )

    # Validate store exists
    store = await db.fetchone(
        "SELECT store_id FROM stores WHERE store_id = ?", (store_id,)
    )
    if store is None:
        return JSONResponse(status_code=404, content={"detail": "Store not found"})

    # Parse and validate timestamp
    try:
        ts_str = body.timestamp.replace("Z", "+00:00")
        ts = datetime.fromisoformat(ts_str)
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return JSONResponse(
            status_code=422,
            content={"detail": "Invalid timestamp format"},
        )

    now = datetime.now(timezone.utc)
    if ts > now + timedelta(hours=1):
        return JSONResponse(
            status_code=422,
            content={"detail": "Timestamp is in the future"},
        )
    if ts < now - timedelta(hours=24):
        return JSONResponse(
            status_code=422,
            content={"detail": "Timestamp is more than 24h in the past"},
        )

    # Persist transaction
    await db.execute(
        """
        INSERT OR IGNORE INTO pos_transactions
            (transaction_id, store_id, visitor_id, timestamp, amount)
        VALUES (?, ?, ?, ?, ?)
        """,
        (body.transaction_id, store_id, body.visitor_id, ts.isoformat(), body.amount),
    )

    # Mark conversion
    visitor_id = body.visitor_id
    if visitor_id:
        # Direct correlation — mark visitor as converted
        await db.execute(
            """
            UPDATE visitors SET converted = 1
            WHERE visitor_id = ? AND store_id = ?
            """,
            (visitor_id, store_id),
        )
        # Mark the most recent unconverted visit
        visit_row = await db.fetchone(
            """
            SELECT visit_id FROM visits
            WHERE visitor_id = ? AND store_id = ? AND converted = 0
            ORDER BY entry_time DESC LIMIT 1
            """,
            (visitor_id, store_id),
        )
        if visit_row:
            await db.execute(
                "UPDATE visits SET converted = 1 WHERE visit_id = ?",
                (visit_row[0],),
            )
    else:
        # Attempt to correlate via billing queue events within 120s
        rows = await db.fetchall(
            """
            SELECT DISTINCT visitor_id FROM events
            WHERE store_id = ? AND event_type = 'BILLING_QUEUE_JOIN'
              AND timestamp >= ? AND timestamp <= ?
            ORDER BY timestamp DESC
            LIMIT 1
            """,
            (
                store_id,
                (ts - timedelta(seconds=120)).isoformat(),
                ts.isoformat(),
            ),
        )
        if rows:
            correlated_visitor = rows[0][0]
            # Check not already converted for this visit
            already = await db.fetchone(
                "SELECT converted FROM visits WHERE visitor_id = ? AND store_id = ? AND converted = 1",
                (correlated_visitor, store_id),
            )
            if not already:
                await db.execute(
                    "UPDATE visitors SET converted = 1 WHERE visitor_id = ? AND store_id = ?",
                    (correlated_visitor, store_id),
                )
                visit_row = await db.fetchone(
                    """
                    SELECT visit_id FROM visits
                    WHERE visitor_id = ? AND store_id = ? AND converted = 0
                    ORDER BY entry_time DESC LIMIT 1
                    """,
                    (correlated_visitor, store_id),
                )
                if visit_row:
                    await db.execute(
                        "UPDATE visits SET converted = 1 WHERE visit_id = ?",
                        (visit_row[0],),
                    )
                visitor_id = correlated_visitor

    return JSONResponse(
        status_code=201,
        content={
            "transaction_id": body.transaction_id,
            "store_id": store_id,
            "visitor_id": visitor_id,
            "converted": visitor_id is not None,
        },
    )
