"""
Export validated event_log.jsonl from the seeded SQLite database.

Produces: event_log.jsonl at the project root.
Each line is a valid JSON object matching the canonical event schema.
"""

import asyncio
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.database import Database

DB_PATH = str(Path(__file__).resolve().parent.parent.parent / "data" / "reintellect.db")
OUTPUT_PATH = Path(__file__).resolve().parent.parent.parent / "event_log.jsonl"

# All valid event types per spec
VALID_EVENT_TYPES = {
    "ENTRY", "EXIT", "ZONE_ENTER", "ZONE_EXIT", "ZONE_DWELL",
    "BILLING_QUEUE_JOIN", "BILLING_QUEUE_ABANDON", "REENTRY",
}


def validate_record(record: dict, index: int) -> list[str]:
    """Validate a single event record. Return list of errors."""
    errors = []
    required = ["event_id", "event_type", "store_id", "visitor_id",
                "timestamp", "camera_id", "attributes"]

    for field in required:
        if field not in record:
            errors.append(f"[{index}] missing field: {field}")

    if "event_type" in record and record["event_type"] not in VALID_EVENT_TYPES:
        errors.append(f"[{index}] invalid event_type: {record['event_type']}")

    if "timestamp" in record:
        try:
            datetime.fromisoformat(record["timestamp"].replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            errors.append(f"[{index}] invalid timestamp: {record['timestamp']}")

    if "event_id" in record:
        try:
            uuid.UUID(str(record["event_id"]))
        except ValueError:
            errors.append(f"[{index}] invalid event_id (not UUID): {record['event_id']}")

    if "visitor_id" in record and not record["visitor_id"]:
        errors.append(f"[{index}] empty visitor_id")

    if "attributes" in record and not isinstance(record["attributes"], dict):
        errors.append(f"[{index}] attributes must be an object")

    return errors


async def main() -> None:
    import logging
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    if not Path(DB_PATH).exists():
        print(f"ERROR: database not found at {DB_PATH}")
        sys.exit(1)

    db = Database()
    await db.connect(DB_PATH)

    rows = await db.fetchall(
        """
        SELECT event_id, event_type, store_id, visitor_id,
               timestamp, camera_id, attributes_json
        FROM events
        ORDER BY timestamp ASC
        """
    )

    records = []
    for row in rows:
        try:
            attrs = json.loads(row[6]) if row[6] else {}
        except (json.JSONDecodeError, TypeError):
            attrs = {}

        records.append({
            "event_id": row[0],
            "event_type": row[1],
            "store_id": row[2],
            "visitor_id": row[3],
            "timestamp": row[4],
            "camera_id": row[5],
            "attributes": attrs,
        })

    await db.close()

    # Validate all records
    all_errors = []
    for i, rec in enumerate(records):
        errs = validate_record(rec, i)
        all_errors.extend(errs)

    print(f"\n{'='*60}")
    print(f"Event log validation report")
    print(f"{'='*60}")
    print(f"  Total records    : {len(records)}")

    # Count by type
    type_counts: dict[str, int] = {}
    for r in records:
        t = r["event_type"]
        type_counts[t] = type_counts.get(t, 0) + 1

    for et in sorted(VALID_EVENT_TYPES):
        print(f"  {et:<30}: {type_counts.get(et, 0)}")

    print(f"\n  Validation errors: {len(all_errors)}")
    if all_errors:
        for e in all_errors[:20]:
            print(f"    {e}")
        if len(all_errors) > 20:
            print(f"    ... and {len(all_errors) - 20} more")
        sys.exit(1)

    # Write JSONL
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"\n  Output           : {OUTPUT_PATH}")
    print(f"  All records valid: YES")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(main())
