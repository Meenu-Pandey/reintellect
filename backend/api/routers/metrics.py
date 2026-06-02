"""
Store metrics endpoint.

GET /stores/{id}/metrics — Return KPIs for a time window.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse

from api.dependencies import get_db
from db.database import Database

router = APIRouter()


@router.get("/stores/{store_id}/metrics")
async def get_metrics(
    store_id: str,
    request: Request,
    start: str | None = Query(None),
    end: str | None = Query(None),
    db: Database | None = Depends(get_db),
) -> JSONResponse:
    """Return store KPIs for a time window.

    Defaults to current calendar day (UTC) if no start/end provided.
    Returns 404 if store not found.
    """
    if db is None:
        return JSONResponse(status_code=503, content={"detail": "Database unavailable"})

    # Validate store exists
    store = await db.fetchone("SELECT store_id, timezone FROM stores WHERE store_id = ?", (store_id,))
    if store is None:
        return JSONResponse(status_code=404, content={"detail": "Store not found"})

    # Parse time window
    now = datetime.now(timezone.utc)
    if start:
        try:
            start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
        except ValueError:
            return JSONResponse(status_code=400, content={"detail": "Invalid start format"})
    else:
        start_dt = now.replace(hour=0, minute=0, second=0, microsecond=0)

    if end:
        try:
            end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
        except ValueError:
            return JSONResponse(status_code=400, content={"detail": "Invalid end format"})
    else:
        end_dt = now

    start_str = start_dt.isoformat()
    end_str = end_dt.isoformat()

    # Unique visitors
    row = await db.fetchone(
        """
        SELECT COUNT(DISTINCT visitor_id) FROM events
        WHERE store_id = ? AND event_type = 'ENTRY'
          AND timestamp >= ? AND timestamp <= ?
        """,
        (store_id, start_str, end_str),
    )
    unique_visitors = row[0] if row else 0

    # Conversions
    row = await db.fetchone(
        """
        SELECT COUNT(DISTINCT visitor_id) FROM visitors
        WHERE store_id = ? AND converted = 1 AND last_seen >= ? AND last_seen <= ?
        """,
        (store_id, start_str, end_str),
    )
    conversions = row[0] if row else 0

    # Conversion rate
    conversion_rate = (conversions / unique_visitors * 100) if unique_visitors > 0 else 0.0

    # Average dwell per zone
    rows = await db.fetchall(
        """
        SELECT json_extract(attributes_json, '$.zone_id') as zone_id,
               AVG(json_extract(attributes_json, '$.dwell_seconds')) as avg_dwell
        FROM events
        WHERE store_id = ? AND event_type IN ('ZONE_EXIT', 'ZONE_DWELL')
          AND timestamp >= ? AND timestamp <= ?
        GROUP BY zone_id
        """,
        (store_id, start_str, end_str),
    )
    avg_dwell_per_zone = {r[0]: round(r[1], 1) for r in rows if r[0] and r[1]}

    # Queue depth (current joiners minus leavers/abandons)
    row = await db.fetchone(
        """
        SELECT COUNT(*) FROM events
        WHERE store_id = ? AND event_type = 'BILLING_QUEUE_JOIN'
          AND timestamp >= ? AND timestamp <= ?
        """,
        (store_id, start_str, end_str),
    )
    queue_joins = row[0] if row else 0

    row = await db.fetchone(
        """
        SELECT COUNT(*) FROM events
        WHERE store_id = ? AND event_type = 'BILLING_QUEUE_ABANDON'
          AND timestamp >= ? AND timestamp <= ?
        """,
        (store_id, start_str, end_str),
    )
    queue_abandons = row[0] if row else 0

    # Abandonment rate
    abandonment_rate = (queue_abandons / queue_joins * 100) if queue_joins > 0 else 0.0

    # Average visit duration
    row = await db.fetchone(
        """
        SELECT AVG(duration_seconds) FROM visits
        WHERE store_id = ? AND duration_seconds IS NOT NULL
          AND entry_time >= ? AND entry_time <= ?
        """,
        (store_id, start_str, end_str),
    )
    avg_visit_duration_seconds = round(row[0], 1) if row and row[0] else 0.0

    # Peak hour
    rows = await db.fetchall(
        """
        SELECT strftime('%H', timestamp) as hour, COUNT(*) as cnt
        FROM events
        WHERE store_id = ? AND event_type = 'ENTRY'
          AND timestamp >= ? AND timestamp <= ?
        GROUP BY hour
        ORDER BY cnt DESC
        LIMIT 1
        """,
        (store_id, start_str, end_str),
    )
    peak_hour = int(rows[0][0]) if rows else None

    return JSONResponse(
        status_code=200,
        content={
            "store_id": store_id,
            "start": start_str,
            "end": end_str,
            "unique_visitors": unique_visitors,
            "conversion_rate": round(conversion_rate, 2),
            "avg_dwell_per_zone": avg_dwell_per_zone,
            "queue_depth": max(0, queue_joins - queue_abandons),
            "abandonment_rate": round(abandonment_rate, 2),
            "avg_visit_duration_seconds": avg_visit_duration_seconds,
            "peak_hour": peak_hour,
        },
    )
