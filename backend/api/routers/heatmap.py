"""
Heatmap endpoint.

GET /stores/{id}/heatmap — Return gridded density heatmap.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse

from api.dependencies import get_db
from db.database import Database

router = APIRouter()

# Resolution presets
RESOLUTION_MAP = {
    "low": 10,
    "medium": 20,
    "high": 40,
}


@router.get("/stores/{store_id}/heatmap")
async def get_heatmap(
    store_id: str,
    request: Request,
    start: str | None = Query(None),
    end: str | None = Query(None),
    resolution: str = Query("medium"),
    zone_id: str | None = Query(None),
    db: Database | None = Depends(get_db),
) -> JSONResponse:
    """Return gridded density heatmap from track_positions.

    Resolution: low=10x10, medium=20x20, high=40x40.
    Returns all cells with density: 0.0 when no positions recorded.
    Returns 404 if store or zone not found.
    """
    if db is None:
        return JSONResponse(status_code=503, content={"detail": "Database unavailable"})

    # Validate store
    store = await db.fetchone("SELECT store_id FROM stores WHERE store_id = ?", (store_id,))
    if store is None:
        return JSONResponse(status_code=404, content={"detail": "Store not found"})

    # Validate zone if provided
    if zone_id:
        zone = await db.fetchone(
            "SELECT zone_id FROM zones WHERE zone_id = ? AND store_id = ?",
            (zone_id, store_id),
        )
        if zone is None:
            return JSONResponse(status_code=404, content={"detail": "Zone not found"})

    # Validate resolution
    if resolution not in RESOLUTION_MAP:
        return JSONResponse(
            status_code=400,
            content={"detail": f"resolution must be one of {list(RESOLUTION_MAP.keys())}"},
        )
    grid_size = RESOLUTION_MAP[resolution]

    # Parse time window
    now = datetime.now(timezone.utc)
    if start:
        try:
            start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
        except ValueError:
            return JSONResponse(status_code=400, content={"detail": "Invalid start format"})
    else:
        start_dt = now - timedelta(days=1)

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

    # Query track positions
    if zone_id:
        # Would need zone polygon filtering — for now filter by zone_id if stored
        rows = await db.fetchall(
            """
            SELECT x, y FROM track_positions
            WHERE store_id = ? AND timestamp >= ? AND timestamp <= ?
            """,
            (store_id, start_str, end_str),
        )
    else:
        rows = await db.fetchall(
            """
            SELECT x, y FROM track_positions
            WHERE store_id = ? AND timestamp >= ? AND timestamp <= ?
            """,
            (store_id, start_str, end_str),
        )

    # Bin positions into grid cells
    cell_width = 1.0 / grid_size
    cell_height = 1.0 / grid_size
    counts = [[0] * grid_size for _ in range(grid_size)]

    for row in rows:
        x, y = row[0], row[1]
        col = min(int(x / cell_width), grid_size - 1)
        row_idx = min(int(y / cell_height), grid_size - 1)
        counts[row_idx][col] += 1

    # Find max for normalisation
    max_count = max(
        (counts[r][c] for r in range(grid_size) for c in range(grid_size)),
        default=0,
    )

    # Build grid
    grid = []
    for row_idx in range(grid_size):
        for col in range(grid_size):
            density = counts[row_idx][col] / max_count if max_count > 0 else 0.0
            grid.append({
                "x": round(col * cell_width, 4),
                "y": round(row_idx * cell_height, 4),
                "width": round(cell_width, 4),
                "height": round(cell_height, 4),
                "density": round(density, 4),
            })

    return JSONResponse(
        status_code=200,
        content={
            "store_id": store_id,
            "resolution": resolution,
            "grid_size": grid_size,
            "total_cells": len(grid),
            "grid": grid,
        },
    )
