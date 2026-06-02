"""
Database initialisation script.

Runs the migration SQL, seeds a demo store layout, then exits.
Used as the `db-init` Docker service command.

Usage:
    python -m db.init_schema
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

# Ensure backend package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.database import Database

logger = logging.getLogger(__name__)

# Default DB path
DEFAULT_DB_PATH = os.environ.get(
    "DB_PATH",
    str(Path(__file__).resolve().parent.parent.parent / "data" / "reintellect.db"),
)

# Migration file
MIGRATION_FILE = Path(__file__).resolve().parent / "migrations" / "001_initial.sql"

# Demo store layout for the Purplle Brigade Road store
DEMO_STORE_LAYOUT = {
    "store_id": "purplle-brigade-road",
    "name": "Purplle Brigade Road",
    "timezone": "Asia/Kolkata",
    "zones": [
        {
            "zone_id": "ZONE_ENTRY",
            "camera_id": "CAM3",
            "zone_type": "entry",
            "name": "Store Entrance",
            "polygon": [(0.0, 0.3), (0.2, 0.3), (0.2, 0.7), (0.0, 0.7)],
        },
        {
            "zone_id": "ZONE_EXIT",
            "camera_id": "CAM3",
            "zone_type": "exit",
            "name": "Store Exit",
            "polygon": [(0.8, 0.3), (1.0, 0.3), (1.0, 0.7), (0.8, 0.7)],
        },
        {
            "zone_id": "ZONE_MAYBELLINE",
            "camera_id": "CAM2",
            "zone_type": "floor",
            "name": "Maybelline",
            "polygon": [(0.0, 0.0), (0.5, 0.0), (0.5, 0.5), (0.0, 0.5)],
        },
        {
            "zone_id": "ZONE_LAKME",
            "camera_id": "CAM2",
            "zone_type": "floor",
            "name": "Lakme",
            "polygon": [(0.5, 0.0), (1.0, 0.0), (1.0, 0.5), (0.5, 0.5)],
        },
        {
            "zone_id": "ZONE_QUEUE",
            "camera_id": "CAM1",
            "zone_type": "billing_queue",
            "name": "Checkout Queue",
            "polygon": [(0.3, 0.4), (0.7, 0.4), (0.7, 0.7), (0.3, 0.7)],
        },
    ],
    "cameras": [
        {"camera_id": "CAM1", "name": "Checkout / POS Area", "position": "ceiling"},
        {"camera_id": "CAM2", "name": "Cosmetics / Makeup Zone", "position": "ceiling"},
        {"camera_id": "CAM3", "name": "Entrance Camera", "position": "ceiling"},
        {"camera_id": "CAM4", "name": "Backroom / Restricted", "position": "ceiling"},
        {"camera_id": "CAM5", "name": "Skincare Zone", "position": "ceiling"},
    ],
}


async def main() -> None:
    """Run migrations and seed demo data."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    db_path = DEFAULT_DB_PATH
    logger.info("Initialising database at: %s", db_path)

    # Ensure directory exists
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    # Connect
    db = Database()
    await db.connect(db_path)

    try:
        # Run migration
        if not MIGRATION_FILE.exists():
            logger.error("Migration file not found: %s", MIGRATION_FILE)
            sys.exit(1)

        migration_sql = MIGRATION_FILE.read_text(encoding="utf-8")
        await db.executescript(migration_sql)
        logger.info("Migration 001_initial.sql applied")

        # Seed demo store
        await db.upsert_store(DEMO_STORE_LAYOUT)
        logger.info("Demo store seeded: %s", DEMO_STORE_LAYOUT["store_id"])

        # Verify
        row = await db.fetchone(
            "SELECT store_id, name FROM stores WHERE store_id = ?",
            (DEMO_STORE_LAYOUT["store_id"],),
        )
        if row:
            logger.info("Verified: store '%s' exists in database", row[1])
        else:
            logger.error("Verification failed: demo store not found")
            sys.exit(1)

    finally:
        await db.close()

    logger.info("Database initialisation complete")


if __name__ == "__main__":
    asyncio.run(main())
