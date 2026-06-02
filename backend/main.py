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

from api.app import create_api_app
from api.websocket.manager import ConnectionManager
from db.database import Database
from db.event_consumer import event_consumer
from detection.demo_source import DemoVideoSource
from detection.pipeline import DetectionPipeline
from engine.event_engine import EventEngine

logger = logging.getLogger(__name__)

# Default database path
DEFAULT_DB_PATH = os.environ.get(
    "DB_PATH",
    str(Path(__file__).resolve().parent.parent / "data" / "reintellect.db"),
)


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


def _build_store_layout() -> dict:
    """Build store layout from environment or defaults.

    In production, this is loaded from the database.
    For now, use a default layout based on the Purplle store CAM3 entrance.
    """
    return {
        "store_id": os.environ.get("STORE_ID", "purplle-brigade-road"),
        "entry_zone": {
            "polygon": [(0.0, 0.3), (0.2, 0.3), (0.2, 0.7), (0.0, 0.7)],
        },
        "exit_zone": {
            "polygon": [(0.8, 0.3), (1.0, 0.3), (1.0, 0.7), (0.8, 0.7)],
        },
        "zones": [
            {
                "zone_id": "ZONE_MAYBELLINE",
                "polygon": [(0.2, 0.0), (0.5, 0.0), (0.5, 0.4), (0.2, 0.4)],
            },
            {
                "zone_id": "ZONE_LAKME",
                "polygon": [(0.5, 0.0), (0.8, 0.0), (0.8, 0.4), (0.5, 0.4)],
            },
            {
                "zone_id": "ZONE_SKINCARE",
                "polygon": [(0.2, 0.6), (0.8, 0.6), (0.8, 1.0), (0.2, 1.0)],
            },
        ],
        "queue_zone": {
            "zone_id": "ZONE_QUEUE",
            "polygon": [(0.6, 0.4), (0.8, 0.4), (0.8, 0.6), (0.6, 0.6)],
        },
        "adjacency_map": {
            "ZONE_MAYBELLINE": ["ZONE_LAKME"],
            "ZONE_LAKME": ["ZONE_MAYBELLINE", "ZONE_QUEUE"],
            "ZONE_SKINCARE": [],
            "ZONE_QUEUE": ["ZONE_LAKME"],
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

    # --- Database ---
    db: Database | None = None
    db_path = DEFAULT_DB_PATH
    if Path(db_path).exists():
        db = Database()
        await db.connect(db_path)
        logger.info("Database connected: %s", db_path)
    else:
        logger.warning(
            "Database not found at %s — run 'python -m db.init_schema' first. "
            "Events will not be persisted.",
            db_path,
        )
    app.state.db = db

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

    # --- EventEngine ---
    store_layout = _build_store_layout()
    engine = EventEngine(track_queue, event_queue, store_layout)
    engine_task = asyncio.create_task(engine.run())
    app.state.engine_task = engine_task
    logger.info("EventEngine started")

    # --- WebSocket ConnectionManager ---
    ws_manager = ConnectionManager()
    app.state.ws_manager = ws_manager
    logger.info("ConnectionManager initialised")

    # --- Event Consumer ---
    consumer_task = asyncio.create_task(
        event_consumer(event_queue, db, ws_manager=ws_manager)
    )
    app.state.consumer_task = consumer_task
    logger.info("event_consumer started")

    logger.info("ReIntellect backend ready")

    yield  # Application runs here

    # --- Shutdown ---
    logger.info("ReIntellect backend shutting down")

    # Cancel consumer first (downstream)
    if consumer_task is not None and not consumer_task.done():
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            logger.info("event_consumer task cancelled")

    # Cancel engine
    if engine_task is not None and not engine_task.done():
        engine_task.cancel()
        try:
            await engine_task
        except asyncio.CancelledError:
            logger.info("EventEngine task cancelled")

    # Cancel pipeline
    if pipeline_task is not None and not pipeline_task.done():
        pipeline_task.cancel()
        try:
            await pipeline_task
        except asyncio.CancelledError:
            logger.info("DetectionPipeline task cancelled")

    # Close database
    if db is not None:
        await db.close()

    logger.info("ReIntellect backend stopped")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    application = FastAPI(
        title="ReIntellect Intelligence API",
        version="0.1.0",
        description="AI-powered Store Intelligence Platform",
        lifespan=lifespan,
    )
    # Wire in middleware and routers
    create_api_app(application)
    return application


app = create_app()
