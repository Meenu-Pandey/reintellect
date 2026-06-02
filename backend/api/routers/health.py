"""
Health check endpoint.

Returns subsystem health status with live probes.
"""

from __future__ import annotations

import time

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()

# App start time (set on first import — close enough)
_start_time = time.time()


@router.get("/health")
async def health_check(request: Request) -> JSONResponse:
    """Return health status of all subsystems.

    Performs live probes:
    - database: SELECT 1
    - detection_pipeline: asyncio task is running
    - event_engine: asyncio task is running

    Returns 200 if all healthy, 503 if any subsystem is unhealthy.
    """
    uptime_seconds = round(time.time() - _start_time, 1)

    # --- Database probe ---
    db = getattr(request.app.state, "db", None)
    db_status = "healthy"
    if db is None:
        db_status = "unhealthy"
    else:
        try:
            row = await db.fetchone("SELECT 1")
            if row is None:
                db_status = "unhealthy"
        except Exception:
            db_status = "unhealthy"

    # --- Detection pipeline probe ---
    pipeline_task = getattr(request.app.state, "pipeline_task", None)
    if pipeline_task is not None and not pipeline_task.done():
        pipeline_status = "healthy"
    else:
        pipeline_status = "unhealthy"

    # --- Event engine probe ---
    engine_task = getattr(request.app.state, "engine_task", None)
    if engine_task is not None and not engine_task.done():
        engine_status = "healthy"
    else:
        engine_status = "unhealthy"

    # Determine overall status
    all_healthy = all(
        s == "healthy" for s in [db_status, pipeline_status, engine_status]
    )
    overall_status = "healthy" if all_healthy else "degraded"
    status_code = 200 if all_healthy else 503

    body = {
        "status": overall_status,
        "version": "0.1.0",
        "uptime_seconds": uptime_seconds,
        "database": db_status,
        "detection_pipeline": pipeline_status,
        "event_engine": engine_status,
    }

    return JSONResponse(content=body, status_code=status_code)
