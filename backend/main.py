"""
ReIntellect backend entrypoint.

Wires together the detection pipeline, event engine, and FastAPI application.
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from detection.demo_source import DemoVideoSource
from detection.pipeline import DetectionPipeline

logger = logging.getLogger(__name__)


def _build_pipeline_config() -> dict:
    """Build pipeline configuration from environment variables."""
    return {
        "camera_id": os.environ.get("CAMERA_ID", "CAM1"),
        "confidence_threshold": float(
            os.environ.get("DETECTION_CONFIDENCE", "0.5")
        ),
        "min_bbox_height_px": int(
            os.environ.get("DETECTION_MIN_HEIGHT", "50")
        ),
        "max_lost_frames": int(
            os.environ.get("TRACK_MAX_LOST_FRAMES", "30")
        ),
        "reconnect_interval": float(
            os.environ.get("RECONNECT_INTERVAL", "2.0")
        ),
        "staff_colour": {
            "hsv_lower": [140, 50, 50],
            "hsv_upper": [170, 255, 255],
            "threshold": 0.15,
        },
    }


def _resolve_video_source() -> DemoVideoSource:
    """Resolve the video source from environment or default."""
    video_source_env = os.environ.get("VIDEO_SOURCE", "demo")
    if video_source_env == "demo":
        # Use default demo clip
        clip_path = (
            Path(__file__).resolve().parent.parent / "resources" / "CAM 1.mp4"
        )
    else:
        clip_path = Path(video_source_env)
    return DemoVideoSource(clip_path)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown."""

    # --- Startup ---
    logger.info("ReIntellect backend starting up")

    # Inter-component communication queues
    track_queue: asyncio.Queue = asyncio.Queue()  # DetectionPipeline → EventEngine
    event_queue: asyncio.Queue = asyncio.Queue()  # EventEngine → event_consumer

    app.state.track_queue = track_queue
    app.state.event_queue = event_queue

    # Database connection placeholder (implemented in Phase 5)
    app.state.db = None

    # --- DetectionPipeline ---
    pipeline_task: asyncio.Task | None = None
    try:
        video_source = _resolve_video_source()
        config = _build_pipeline_config()
        pipeline = DetectionPipeline(
            video_source=video_source,
            track_queue=track_queue,
            config=config,
        )
        pipeline_task = asyncio.create_task(pipeline.run())
        app.state.pipeline_task = pipeline_task
        logger.info("DetectionPipeline started")
    except FileNotFoundError as exc:
        logger.warning(
            "DetectionPipeline not started (video source unavailable): %s", exc
        )
        app.state.pipeline_task = None

    logger.info("ReIntellect backend ready")

    yield  # Application runs here

    # --- Shutdown ---
    logger.info("ReIntellect backend shutting down")

    if pipeline_task is not None and not pipeline_task.done():
        pipeline_task.cancel()
        try:
            await pipeline_task
        except asyncio.CancelledError:
            logger.info("DetectionPipeline task cancelled")

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
