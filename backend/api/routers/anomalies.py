"""
Anomalies endpoint.

GET /stores/{id}/anomalies — Return anomaly records.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse

from api.dependencies import get_db
from db.database import Database

router = APIRouter()


@router.get("/stores/{store_id}/anomalies")
async def get_anomalies(
    store_id: str,
    request: Request,
    start: str | None = Query(None),
    end: str | None = Query(None),
    db: Database | None = Depends(get_db),
) -> JSONResponse:
    """Return anomaly records for a time window.

    Default: last 24h. Max: 24h window.
    Returns up to 500 records ordered by detected_at descending.
    Returns 404 if store not found.
    Returns 400 if date params malformed or start > end.
    """
    if db is None:
        return JSONResponse(status_code=503, content={"detail": "Database unavailable"})

    # Validate store
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
        start_dt = now - timedelta(hours=24)

    if end:
        try:
            end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
        except ValueError:
            return JSONResponse(status_code=400, content={"detail": "Invalid end format"})
    else:
        end_dt = now

    # Validate start <= end
    if start_dt > end_dt:
        return JSONResponse(status_code=400, content={"detail": "start must be <= end"})

    start_str = start_dt.isoformat()
    end_str = end_dt.isoformat()

    # Query anomalies
    rows = await db.fetchall(
        """
        SELECT anomaly_id, anomaly_type, severity, detected_at, description, metadata_json
        FROM anomalies
        WHERE store_id = ? AND detected_at >= ? AND detected_at <= ?
        ORDER BY detected_at DESC
        LIMIT 500
        """,
        (store_id, start_str, end_str),
    )

    anomalies = []
    for row in rows:
        try:
            metadata = json.loads(row[5]) if row[5] else {}
        except (json.JSONDecodeError, TypeError):
            metadata = {}

        anomalies.append({
            "anomaly_id": row[0],
            "anomaly_type": row[1],
            "severity": row[2],
            "detected_at": row[3],
            "description": row[4],
            "metadata": metadata,
        })

    return JSONResponse(
        status_code=200,
        content={
            "store_id": store_id,
            "anomalies": anomalies,
            "count": len(anomalies),
        },
    )
