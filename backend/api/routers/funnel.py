"""
Funnel analytics endpoint.

GET /stores/{id}/funnel — Return visitor funnel stages.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse

from api.dependencies import get_db
from db.database import Database

router = APIRouter()


@router.get("/stores/{store_id}/funnel")
async def get_funnel(
    store_id: str,
    request: Request,
    start: str | None = Query(None),
    end: str | None = Query(None),
    db: Database | None = Depends(get_db),
) -> JSONResponse:
    """Return visitor funnel stages for a time window.

    Max 90-day window. Returns ordered stages with visitor counts,
    entry rates, and average dwell times.

    Returns 404 if store not found.
    Returns 200 with empty list and data_available: false when no events exist.
    """
    if db is None:
        return JSONResponse(status_code=503, content={"detail": "Database unavailable"})

    # Validate store exists
    store = await db.fetchone("SELECT store_id FROM stores WHERE store_id = ?", (store_id,))
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
        start_dt = now - timedelta(days=7)

    if end:
        try:
            end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
        except ValueError:
            return JSONResponse(status_code=400, content={"detail": "Invalid end format"})
    else:
        end_dt = now

    # Max 90-day window
    if (end_dt - start_dt).days > 90:
        return JSONResponse(status_code=400, content={"detail": "Maximum window is 90 days"})

    start_str = start_dt.isoformat()
    end_str = end_dt.isoformat()

    # Total unique visitors entering in window
    row = await db.fetchone(
        """
        SELECT COUNT(DISTINCT visitor_id) FROM events
        WHERE store_id = ? AND event_type = 'ENTRY'
          AND timestamp >= ? AND timestamp <= ?
        """,
        (store_id, start_str, end_str),
    )
    total_visitors = row[0] if row else 0

    if total_visitors == 0:
        return JSONResponse(
            status_code=200,
            content={"stages": [], "data_available": False},
        )

    # Get zone visit stats
    rows = await db.fetchall(
        """
        SELECT json_extract(attributes_json, '$.zone_id') as zone_id,
               COUNT(DISTINCT visitor_id) as visitor_count,
               AVG(json_extract(attributes_json, '$.dwell_seconds')) as avg_dwell
        FROM events
        WHERE store_id = ? AND event_type = 'ZONE_ENTER'
          AND timestamp >= ? AND timestamp <= ?
        GROUP BY zone_id
        ORDER BY visitor_count DESC, zone_id ASC
        """,
        (store_id, start_str, end_str),
    )

    # Get zone names from zones table
    zone_rows = await db.fetchall(
        "SELECT zone_id, name FROM zones WHERE store_id = ?", (store_id,)
    )
    zone_names = {r[0]: r[1] for r in zone_rows}

    # Get average dwell from ZONE_EXIT/ZONE_DWELL events
    dwell_rows = await db.fetchall(
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
    dwell_map = {r[0]: r[1] for r in dwell_rows if r[0] and r[1]}

    # Build funnel stages
    stages = []
    for row in rows:
        zone_id = row[0]
        if zone_id is None:
            continue
        visitor_count = row[1]
        entry_rate = round(visitor_count / total_visitors, 4) if total_visitors > 0 else 0.0
        avg_dwell = round(dwell_map.get(zone_id, 0.0), 1)

        stages.append({
            "zone_id": zone_id,
            "zone_name": zone_names.get(zone_id, zone_id),
            "visitor_count": visitor_count,
            "entry_rate": entry_rate,
            "avg_dwell_seconds": avg_dwell,
        })

    # Get conversion funnel
    converted_rows = await db.fetchall(
        """
        SELECT json_extract(e.attributes_json, '$.zone_id') as zone_id,
               COUNT(DISTINCT e.visitor_id) as converted_count
        FROM events e
        JOIN visitors v ON e.visitor_id = v.visitor_id
        WHERE e.store_id = ? AND e.event_type = 'ZONE_ENTER'
          AND v.converted = 1
          AND e.timestamp >= ? AND e.timestamp <= ?
        GROUP BY zone_id
        """,
        (store_id, start_str, end_str),
    )
    conversion_funnel = {r[0]: r[1] for r in converted_rows if r[0]}

    return JSONResponse(
        status_code=200,
        content={
            "stages": stages,
            "conversion_funnel": conversion_funnel,
            "data_available": True,
            "total_visitors": total_visitors,
        },
    )
