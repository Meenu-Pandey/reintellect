"""
FastAPI application factory with middleware.

Creates the FastAPI app with:
- CORSMiddleware (allow frontend origin from env)
- RequestIDMiddleware (UUID v4 per request in contextvars)
- StructuredLoggingMiddleware (JSON log per request)
"""

from __future__ import annotations

import contextvars
import json
import logging
import os
import time
import uuid
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from api.routers import health, schema

logger = logging.getLogger(__name__)

# Context variable for request ID
request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id", default=""
)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Assigns a UUID v4 request_id to each request via contextvars."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        rid = str(uuid.uuid4())
        request_id_var.set(rid)
        request.state.request_id = rid
        response = await call_next(request)
        response.headers["X-Request-ID"] = rid
        return response


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """Logs each request as a structured JSON line."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000

        rid = getattr(request.state, "request_id", "")
        log_entry: dict[str, Any] = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
            "request_id": rid,
        }
        logger.info(json.dumps(log_entry))
        return response


def create_api_app(app: FastAPI) -> None:
    """Configure middleware and include routers on the given FastAPI app.

    This is called during lifespan setup to wire in the API layer.

    Args:
        app: The FastAPI application instance.
    """
    # --- CORS ---
    frontend_origin = os.environ.get("FRONTEND_ORIGIN", "http://localhost:3000")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[frontend_origin, "*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Custom middleware (added in reverse order — last added runs first) ---
    app.add_middleware(StructuredLoggingMiddleware)
    app.add_middleware(RequestIDMiddleware)

    # --- Routers ---
    app.include_router(health.router)
    app.include_router(schema.router)
