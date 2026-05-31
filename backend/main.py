"""
ReIntellect backend entrypoint.

Wires together the detection pipeline, event engine, and FastAPI application.
"""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown."""

    # --- Startup ---
    logger.info("ReIntellect backend starting up")

    # Inter-component communication queues (stubs — wired in later tasks)
    track_queue: asyncio.Queue = asyncio.Queue()  # DetectionPipeline → EventEngine
    event_queue: asyncio.Queue = asyncio.Queue()  # EventEngine → event_consumer

    app.state.track_queue = track_queue
    app.state.event_queue = event_queue

    # Database connection placeholder (implemented in Phase 5)
    app.state.db = None

    logger.info("ReIntellect backend ready")

    yield  # Application runs here

    # --- Shutdown ---
    logger.info("ReIntellect backend shutting down")
    logger.info("ReIntellect backend stopped")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    application = FastAPI(
        title="ReIntellect Intelligence API",
        version="0.1.0",
        description="AI-powered Store Intelligence Platform",
        lifespan=lifespan,
    )
    return application


app = create_app()
