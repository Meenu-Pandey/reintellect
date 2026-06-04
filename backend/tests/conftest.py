"""
Shared pytest fixtures for the ReIntellect test suite.

Provides:
- in_memory_db: aiosqlite in-memory DB with schema applied
- test_client: Starlette TestClient with a fully wired test app
- sample_store_layout: dict with 4 zones matching test polygon coordinates
- mock_pipeline: asyncio.Queue stub replacing DetectionPipeline
"""

from __future__ import annotations

import os
import sqlite3
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest
from hypothesis import HealthCheck, settings
from starlette.testclient import TestClient

# ---------------------------------------------------------------------------
# Hypothesis CI profile
# ---------------------------------------------------------------------------

settings.register_profile(
    "ci",
    max_examples=100,
    suppress_health_check=[HealthCheck.too_slow],
)
settings.load_profile("ci")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MIGRATION_FILE = (
    Path(__file__).resolve().parent.parent / "db" / "migrations" / "001_initial.sql"
)

DEMO_STORE_ID = "test-store"


def _apply_schema(db_path: str) -> None:
    """Apply the migration SQL to a SQLite file."""
    conn = sqlite3.connect(db_path)
    conn.executescript(MIGRATION_FILE.read_text(encoding="utf-8"))
    conn.execute(
        "INSERT INTO stores (store_id, name, timezone) VALUES (?, ?, ?)",
        (DEMO_STORE_ID, "Test Store", "UTC"),
    )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# sample_store_layout
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_store_layout() -> dict:
    """A store layout dict with 4 zones suitable for integration tests."""
    return {
        "store_id": DEMO_STORE_ID,
        "name": "Test Store",
        "timezone": "UTC",
        "entry_zone": {
            "polygon": [(0.0, 0.0), (0.2, 0.0), (0.2, 0.2), (0.0, 0.2)],
        },
        "exit_zone": {
            "polygon": [(0.8, 0.8), (1.0, 0.8), (1.0, 1.0), (0.8, 1.0)],
        },
        "zones": [
            {
                "zone_id": "ZONE_MAKEUP",
                "polygon": [(0.3, 0.3), (0.6, 0.3), (0.6, 0.6), (0.3, 0.6)],
            },
            {
                "zone_id": "ZONE_SKINCARE",
                "polygon": [(0.1, 0.6), (0.5, 0.6), (0.5, 0.9), (0.1, 0.9)],
            },
        ],
        "queue_zone": {
            "zone_id": "ZONE_QUEUE",
            "polygon": [(0.7, 0.0), (1.0, 0.0), (1.0, 0.3), (0.7, 0.3)],
        },
        "adjacency_map": {
            "ZONE_MAKEUP": ["ZONE_SKINCARE"],
            "ZONE_SKINCARE": ["ZONE_MAKEUP"],
        },
    }


# ---------------------------------------------------------------------------
# in_memory_db
# ---------------------------------------------------------------------------

@pytest.fixture
async def in_memory_db():
    """Async aiosqlite connection with schema applied (in-memory via temp file)."""
    from db.database import Database

    db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_path = db_file.name
    db_file.close()

    _apply_schema(db_path)

    db = Database()
    await db.connect(db_path)
    yield db
    await db.close()

    try:
        os.unlink(db_path)
    except OSError:
        pass


# ---------------------------------------------------------------------------
# mock_pipeline
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_pipeline():
    """asyncio.Queue stub replacing DetectionPipeline.track_queue."""
    import asyncio
    return asyncio.Queue()


# ---------------------------------------------------------------------------
# test_client  (module-scoped for speed — shares DB across tests in a module)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def test_client():
    """Starlette TestClient with a fully wired test app backed by a temp DB."""
    db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_path = db_file.name
    db_file.close()

    # Apply schema FIRST before the app tries to open the DB
    _apply_schema(db_path)

    # Now set the env var so main.py picks it up
    os.environ["DB_PATH"] = db_path
    os.environ["VIDEO_SOURCE"] = "none"

    # Import fresh after env vars are set
    import importlib
    import main as main_module
    importlib.reload(main_module)
    app = main_module.create_app()

    with TestClient(app) as client:
        yield client

    # Clean up env vars after module scope
    os.environ.pop("DB_PATH", None)
    os.environ.pop("VIDEO_SOURCE", None)

    try:
        os.unlink(db_path)
    except OSError:
        pass
