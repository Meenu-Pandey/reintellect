"""
Async SQLite database connection manager.

Provides async access to the ReIntellect SQLite database via aiosqlite.
Supports idempotent event upsert and store layout upsert.
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any

import aiosqlite

from engine.models import Event

logger = logging.getLogger(__name__)


class Database:
    """Async SQLite database wrapper.

    Provides connection management, query execution, and domain-specific
    upsert methods for events and store layouts.
    """

    def __init__(self) -> None:
        self._conn: aiosqlite.Connection | None = None
        self._db_path: str | None = None

    async def connect(self, db_path: str) -> None:
        """Open a connection to the SQLite database.

        Enables WAL mode and foreign keys on connection.

        Args:
            db_path: Path to the SQLite database file.
        """
        self._db_path = db_path
        self._conn = await aiosqlite.connect(db_path)
        await self._conn.execute("PRAGMA journal_mode=WAL")
        await self._conn.execute("PRAGMA foreign_keys=ON")
        self._conn.row_factory = aiosqlite.Row
        logger.info("Database connected: %s", db_path)

    async def close(self) -> None:
        """Close the database connection."""
        if self._conn is not None:
            await self._conn.close()
            self._conn = None
            logger.info("Database closed")

    async def execute(self, sql: str, params: tuple | list = ()) -> None:
        """Execute a SQL statement.

        Args:
            sql: SQL statement.
            params: Query parameters.
        """
        assert self._conn is not None, "Database not connected"
        await self._conn.execute(sql, params)
        await self._conn.commit()

    async def executemany(self, sql: str, params_list: list) -> None:
        """Execute a SQL statement with multiple parameter sets.

        Args:
            sql: SQL statement.
            params_list: List of parameter tuples.
        """
        assert self._conn is not None, "Database not connected"
        await self._conn.executemany(sql, params_list)
        await self._conn.commit()

    async def executescript(self, sql: str) -> None:
        """Execute a multi-statement SQL script.

        Args:
            sql: SQL script (multiple statements separated by semicolons).
        """
        assert self._conn is not None, "Database not connected"
        await self._conn.executescript(sql)

    async def fetchall(self, sql: str, params: tuple | list = ()) -> list[Any]:
        """Execute a query and return all rows.

        Args:
            sql: SQL query.
            params: Query parameters.

        Returns:
            List of Row objects.
        """
        assert self._conn is not None, "Database not connected"
        cursor = await self._conn.execute(sql, params)
        return await cursor.fetchall()

    async def fetchone(self, sql: str, params: tuple | list = ()) -> Any | None:
        """Execute a query and return a single row.

        Args:
            sql: SQL query.
            params: Query parameters.

        Returns:
            A single Row object or None.
        """
        assert self._conn is not None, "Database not connected"
        cursor = await self._conn.execute(sql, params)
        return await cursor.fetchone()

    async def upsert_event(self, event: Event) -> None:
        """Idempotently insert an event.

        Uses INSERT OR IGNORE to ensure duplicate event_ids are ignored.
        Also upserts the visitor record.

        Args:
            event: Canonical Event object to persist.
        """
        assert self._conn is not None, "Database not connected"

        timestamp_str = event.timestamp.isoformat()
        attributes_json = json.dumps(event.attributes)

        # Upsert visitor
        await self._conn.execute(
            """
            INSERT INTO visitors (visitor_id, store_id, first_seen, last_seen)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(visitor_id) DO UPDATE SET
                last_seen = MAX(visitors.last_seen, excluded.last_seen)
            """,
            (event.visitor_id, event.store_id, timestamp_str, timestamp_str),
        )

        # Insert event (idempotent by event_id)
        await self._conn.execute(
            """
            INSERT OR IGNORE INTO events
                (event_id, event_type, store_id, visitor_id, timestamp, camera_id, attributes_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.event_id,
                event.event_type,
                event.store_id,
                event.visitor_id,
                timestamp_str,
                event.camera_id,
                attributes_json,
            ),
        )

        # Upsert visit record for ENTRY events
        if event.event_type == "ENTRY":
            visit_id = str(uuid.uuid4())
            await self._conn.execute(
                """
                INSERT OR IGNORE INTO visits
                    (visit_id, visitor_id, store_id, entry_time)
                VALUES (?, ?, ?, ?)
                """,
                (visit_id, event.visitor_id, event.store_id, timestamp_str),
            )

        await self._conn.commit()

    async def upsert_store(self, layout: dict[str, Any]) -> None:
        """Insert or replace store layout (stores, zones, cameras).

        Args:
            layout: Store layout dict with keys:
                - store_id: str
                - name: str
                - timezone: str
                - zones: list of zone dicts
                - cameras: list of camera dicts
        """
        assert self._conn is not None, "Database not connected"

        store_id = layout["store_id"]
        name = layout.get("name", store_id)
        tz = layout.get("timezone", "Asia/Kolkata")

        # Upsert store
        await self._conn.execute(
            """
            INSERT INTO stores (store_id, name, timezone)
            VALUES (?, ?, ?)
            ON CONFLICT(store_id) DO UPDATE SET
                name = excluded.name,
                timezone = excluded.timezone,
                updated_at = datetime('now')
            """,
            (store_id, name, tz),
        )

        # Upsert zones
        zones = layout.get("zones", [])
        for zone in zones:
            polygon_json = json.dumps(zone.get("polygon", []))
            await self._conn.execute(
                """
                INSERT INTO zones (zone_id, store_id, camera_id, zone_type, name, polygon_json)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(zone_id, store_id) DO UPDATE SET
                    camera_id = excluded.camera_id,
                    zone_type = excluded.zone_type,
                    name = excluded.name,
                    polygon_json = excluded.polygon_json
                """,
                (
                    zone["zone_id"],
                    store_id,
                    zone.get("camera_id"),
                    zone.get("zone_type", "floor"),
                    zone.get("name", zone["zone_id"]),
                    polygon_json,
                ),
            )

        # Upsert cameras
        cameras = layout.get("cameras", [])
        for camera in cameras:
            await self._conn.execute(
                """
                INSERT INTO cameras (camera_id, store_id, name, position)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(camera_id, store_id) DO UPDATE SET
                    name = excluded.name,
                    position = excluded.position
                """,
                (
                    camera["camera_id"],
                    store_id,
                    camera.get("name"),
                    camera.get("position"),
                ),
            )

        await self._conn.commit()
        logger.info("Store layout upserted: %s", store_id)
