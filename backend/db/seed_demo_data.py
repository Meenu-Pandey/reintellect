"""
Demo data seeder for hackathon demonstration.

Populates the database with a realistic day of Purplle store activity:
- ~200 visitors across 10-hour operating day (10am-8pm IST)
- ENTRY/EXIT events with hourly distribution
- ZONE_ENTER/ZONE_EXIT/ZONE_DWELL events across brand zones
- track_positions for heatmap density
- BILLING_QUEUE_JOIN/ABANDON events
- POS transactions with conversions
- Anomaly records

Usage:
    python -m db.seed_demo_data
"""

from __future__ import annotations

import asyncio
import json
import logging
import math
import os
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.database import Database

logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = os.environ.get(
    "DB_PATH",
    str(Path(__file__).resolve().parent.parent.parent / "data" / "reintellect.db"),
)

STORE_ID = "purplle-brigade-road"

# Zone definitions with centroid hotspots for heatmap
ZONES = {
    "ZONE_MAYBELLINE": {"centroid": (0.35, 0.2), "spread": 0.08, "popularity": 0.7},
    "ZONE_LAKME": {"centroid": (0.65, 0.2), "spread": 0.08, "popularity": 0.85},
    "ZONE_SKINCARE": {"centroid": (0.5, 0.75), "spread": 0.12, "popularity": 0.5},
    "ZONE_QUEUE": {"centroid": (0.7, 0.5), "spread": 0.05, "popularity": 0.4},
}

# Hourly visitor distribution (10am-8pm, 10 hours)
HOURLY_DISTRIBUTION = [12, 15, 22, 30, 18, 14, 20, 35, 25, 15]  # Total ~206


def _random_timestamp(base: datetime, hour_offset: int) -> datetime:
    """Generate a random timestamp within a given hour."""
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    return base + timedelta(hours=hour_offset, minutes=minute, seconds=second)


def _gauss_point(cx: float, cy: float, spread: float) -> tuple[float, float]:
    """Generate a gaussian-distributed point around a centroid."""
    x = max(0.0, min(1.0, random.gauss(cx, spread)))
    y = max(0.0, min(1.0, random.gauss(cy, spread)))
    return (x, y)


async def seed_demo_data() -> None:
    """Seed the database with realistic demo data."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    db_path = DEFAULT_DB_PATH
    if not Path(db_path).exists():
        logger.error("Database not found at %s — run 'python -m db.init_schema' first", db_path)
        sys.exit(1)

    db = Database()
    await db.connect(db_path)

    try:
        # Clear existing demo data
        await db.execute("DELETE FROM track_positions WHERE store_id = ?", (STORE_ID,))
        await db.execute("DELETE FROM anomalies WHERE store_id = ?", (STORE_ID,))
        await db.execute("DELETE FROM pos_transactions WHERE store_id = ?", (STORE_ID,))
        await db.execute("DELETE FROM events WHERE store_id = ?", (STORE_ID,))
        await db.execute("DELETE FROM visits WHERE store_id = ?", (STORE_ID,))
        await db.execute("DELETE FROM visitors WHERE store_id = ?", (STORE_ID,))
        logger.info("Cleared existing demo data")

        # Base time: today at 10:00 IST (04:30 UTC)
        now = datetime.now(timezone.utc)
        base_date = now.replace(hour=4, minute=30, second=0, microsecond=0)
        if base_date > now:
            base_date -= timedelta(days=1)

        all_visitors = []
        all_events = []
        all_positions = []
        all_transactions = []

        # Generate visitors hour by hour
        for hour_idx, visitor_count in enumerate(HOURLY_DISTRIBUTION):
            for _ in range(visitor_count):
                visitor_id = str(uuid.uuid4())
                entry_time = _random_timestamp(base_date, hour_idx)
                visit_duration = random.gauss(300, 120)  # ~5 min avg, 2 min std
                visit_duration = max(60, min(900, visit_duration))
                exit_time = entry_time + timedelta(seconds=visit_duration)

                all_visitors.append({
                    "visitor_id": visitor_id,
                    "entry_time": entry_time,
                    "exit_time": exit_time,
                    "duration": visit_duration,
                })

                # ENTRY event
                all_events.append({
                    "event_id": str(uuid.uuid4()),
                    "event_type": "ENTRY",
                    "store_id": STORE_ID,
                    "visitor_id": visitor_id,
                    "timestamp": entry_time.isoformat(),
                    "camera_id": "CAM3",
                    "attributes_json": "{}",
                })

                # Zone visits (1-3 zones per visitor)
                zones_to_visit = random.sample(
                    list(ZONES.keys()),
                    k=min(random.randint(1, 3), len(ZONES)),
                )
                # Weight by popularity
                zones_to_visit = [
                    z for z in zones_to_visit
                    if random.random() < ZONES[z]["popularity"]
                ]
                if not zones_to_visit:
                    zones_to_visit = [random.choice(list(ZONES.keys()))]

                current_time = entry_time + timedelta(seconds=random.randint(10, 30))

                for zone_id in zones_to_visit:
                    zone_info = ZONES[zone_id]
                    dwell = random.gauss(45, 20)
                    dwell = max(5, min(180, dwell))

                    zone_enter_time = current_time
                    zone_exit_time = zone_enter_time + timedelta(seconds=dwell)

                    if zone_exit_time > exit_time:
                        break

                    camera_id = "CAM2" if "MAYBELLINE" in zone_id or "LAKME" in zone_id else "CAM5" if "SKINCARE" in zone_id else "CAM1"

                    # ZONE_ENTER
                    all_events.append({
                        "event_id": str(uuid.uuid4()),
                        "event_type": "ZONE_ENTER",
                        "store_id": STORE_ID,
                        "visitor_id": visitor_id,
                        "timestamp": zone_enter_time.isoformat(),
                        "camera_id": camera_id,
                        "attributes_json": json.dumps({"zone_id": zone_id}),
                    })

                    # ZONE_DWELL (if dwell >= 30s)
                    if dwell >= 30:
                        all_events.append({
                            "event_id": str(uuid.uuid4()),
                            "event_type": "ZONE_DWELL",
                            "store_id": STORE_ID,
                            "visitor_id": visitor_id,
                            "timestamp": (zone_enter_time + timedelta(seconds=30)).isoformat(),
                            "camera_id": camera_id,
                            "attributes_json": json.dumps({"zone_id": zone_id, "dwell_seconds": round(dwell, 1)}),
                        })

                    # ZONE_EXIT
                    all_events.append({
                        "event_id": str(uuid.uuid4()),
                        "event_type": "ZONE_EXIT",
                        "store_id": STORE_ID,
                        "visitor_id": visitor_id,
                        "timestamp": zone_exit_time.isoformat(),
                        "camera_id": camera_id,
                        "attributes_json": json.dumps({"zone_id": zone_id, "dwell_seconds": round(dwell, 1)}),
                    })

                    # Track positions (every ~5s while in zone)
                    pos_time = zone_enter_time
                    while pos_time < zone_exit_time:
                        x, y = _gauss_point(zone_info["centroid"][0], zone_info["centroid"][1], zone_info["spread"])
                        all_positions.append((STORE_ID, visitor_id, camera_id, x, y, pos_time.isoformat()))
                        pos_time += timedelta(seconds=random.uniform(3, 7))

                    current_time = zone_exit_time + timedelta(seconds=random.randint(5, 20))

                # Queue join (~40% of visitors)
                joined_queue = random.random() < 0.40
                if joined_queue and current_time < exit_time:
                    queue_time = current_time
                    all_events.append({
                        "event_id": str(uuid.uuid4()),
                        "event_type": "BILLING_QUEUE_JOIN",
                        "store_id": STORE_ID,
                        "visitor_id": visitor_id,
                        "timestamp": queue_time.isoformat(),
                        "camera_id": "CAM1",
                        "attributes_json": json.dumps({"queue_position": random.randint(1, 4)}),
                    })

                    # ~75% convert, ~25% abandon
                    if random.random() < 0.75:
                        # Purchase
                        txn_time = queue_time + timedelta(seconds=random.randint(30, 90))
                        amount = round(random.uniform(199, 2499), 2)
                        all_transactions.append({
                            "transaction_id": str(uuid.uuid4()),
                            "store_id": STORE_ID,
                            "visitor_id": visitor_id,
                            "timestamp": txn_time.isoformat(),
                            "amount": amount,
                        })
                    else:
                        # Abandon
                        abandon_time = queue_time + timedelta(seconds=random.randint(60, 180))
                        all_events.append({
                            "event_id": str(uuid.uuid4()),
                            "event_type": "BILLING_QUEUE_ABANDON",
                            "store_id": STORE_ID,
                            "visitor_id": visitor_id,
                            "timestamp": abandon_time.isoformat(),
                            "camera_id": "CAM1",
                            "attributes_json": json.dumps({"wait_seconds": random.randint(60, 180)}),
                        })

                # EXIT event
                all_events.append({
                    "event_id": str(uuid.uuid4()),
                    "event_type": "EXIT",
                    "store_id": STORE_ID,
                    "visitor_id": visitor_id,
                    "timestamp": exit_time.isoformat(),
                    "camera_id": "CAM3",
                    "attributes_json": json.dumps({"duration_seconds": round(visit_duration, 1)}),
                })

                # Entry zone track positions
                entry_pos_time = entry_time
                for _ in range(3):
                    x, y = _gauss_point(0.1, 0.5, 0.05)
                    all_positions.append((STORE_ID, visitor_id, "CAM3", x, y, entry_pos_time.isoformat()))
                    entry_pos_time += timedelta(seconds=2)

        # Insert visitors
        for v in all_visitors:
            converted = 1 if any(t["visitor_id"] == v["visitor_id"] for t in all_transactions) else 0
            await db.execute(
                "INSERT OR IGNORE INTO visitors (visitor_id, store_id, first_seen, last_seen, converted) VALUES (?, ?, ?, ?, ?)",
                (v["visitor_id"], STORE_ID, v["entry_time"].isoformat(), v["exit_time"].isoformat(), converted),
            )

        # Insert visits
        for v in all_visitors:
            converted = 1 if any(t["visitor_id"] == v["visitor_id"] for t in all_transactions) else 0
            await db.execute(
                "INSERT OR IGNORE INTO visits (visit_id, visitor_id, store_id, entry_time, exit_time, duration_seconds, converted) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), v["visitor_id"], STORE_ID, v["entry_time"].isoformat(), v["exit_time"].isoformat(), round(v["duration"], 1), converted),
            )

        # Insert events
        for e in all_events:
            await db.execute(
                "INSERT OR IGNORE INTO events (event_id, event_type, store_id, visitor_id, timestamp, camera_id, attributes_json) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (e["event_id"], e["event_type"], e["store_id"], e["visitor_id"], e["timestamp"], e["camera_id"], e["attributes_json"]),
            )

        # Insert track positions
        for pos in all_positions:
            await db.execute(
                "INSERT INTO track_positions (store_id, visitor_id, camera_id, x, y, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                pos,
            )

        # Insert POS transactions
        for txn in all_transactions:
            await db.execute(
                "INSERT OR IGNORE INTO pos_transactions (transaction_id, store_id, visitor_id, timestamp, amount) VALUES (?, ?, ?, ?, ?)",
                (txn["transaction_id"], txn["store_id"], txn["visitor_id"], txn["timestamp"], txn["amount"]),
            )

        # Insert anomalies
        anomalies_data = [
            ("QUEUE_BUILDUP", "high", base_date + timedelta(hours=3, minutes=15), "Queue depth 7 in ZONE_QUEUE sustained for 210s", {"zone_id": "ZONE_QUEUE", "depth": 7, "duration_seconds": 210}),
            ("QUEUE_BUILDUP", "high", base_date + timedelta(hours=7, minutes=45), "Queue depth 6 in ZONE_QUEUE sustained for 195s", {"zone_id": "ZONE_QUEUE", "depth": 6, "duration_seconds": 195}),
            ("EMPTY_STORE", "medium", base_date + timedelta(hours=9, minutes=30), "Store empty for 720s during operating hours", {"visitor_count": 0, "duration_seconds": 720}),
            ("UNUSUAL_DWELL", "low", base_date + timedelta(hours=5, minutes=10), "Visitor in ZONE_LAKME for 1020s (threshold: 900s)", {"zone_id": "ZONE_LAKME", "dwell_seconds": 1020}),
            ("CAMERA_OVERLAP_CONFLICT", "high", base_date + timedelta(hours=4, minutes=22), "Track 47 detected in non-adjacent zones ZONE_MAYBELLINE and ZONE_SKINCARE within 1.2s", {"track_id": 47, "zone_a": "ZONE_MAYBELLINE", "zone_b": "ZONE_SKINCARE", "gap_seconds": 1.2}),
        ]
        for atype, severity, detected_at, desc, meta in anomalies_data:
            await db.execute(
                "INSERT INTO anomalies (anomaly_id, store_id, anomaly_type, severity, detected_at, description, metadata_json) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), STORE_ID, atype, severity, detected_at.isoformat(), desc, json.dumps(meta)),
            )

        # Summary
        logger.info("Seeded demo data:")
        logger.info("  Visitors: %d", len(all_visitors))
        logger.info("  Events: %d", len(all_events))
        logger.info("  Track positions: %d", len(all_positions))
        logger.info("  POS transactions: %d", len(all_transactions))
        logger.info("  Anomalies: %d", len(anomalies_data))
        logger.info("  Conversions: %d (%.1f%%)", len(all_transactions), len(all_transactions) / len(all_visitors) * 100)

    finally:
        await db.close()

    logger.info("Demo data seeding complete")


if __name__ == "__main__":
    asyncio.run(seed_demo_data())
