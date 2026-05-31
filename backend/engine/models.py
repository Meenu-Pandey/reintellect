"""
Canonical event models for the ReIntellect event stream.

The public event schema uses `visitor_id` (not `track_id`).
`event_id` is client-supplied (UUID v4) for idempotent ingestion.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


# The 8 valid event types defined by the challenge specification.
EVENT_TYPES: frozenset[str] = frozenset(
    [
        "ENTRY",
        "EXIT",
        "ZONE_ENTER",
        "ZONE_EXIT",
        "ZONE_DWELL",
        "BILLING_QUEUE_JOIN",
        "BILLING_QUEUE_ABANDON",
        "REENTRY",
    ]
)


@dataclass
class Event:
    """Canonical event object for the ReIntellect event stream.

    Attributes:
        event_id: Client-supplied UUID v4 (idempotency key).
        event_type: One of the 8 valid EVENT_TYPES.
        store_id: Identifier of the store where the event occurred.
        visitor_id: Stable business-level visitor identifier (assigned at ENTRY).
        timestamp: UTC datetime of the event.
        camera_id: Identifier of the camera that observed the event.
        attributes: Event-type-specific fields (e.g. zone_id, dwell_seconds).
    """

    event_id: str
    event_type: str
    store_id: str
    visitor_id: str
    timestamp: datetime
    camera_id: str
    attributes: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.event_type not in EVENT_TYPES:
            raise ValueError(
                f"event_type must be one of {sorted(EVENT_TYPES)}, "
                f"got '{self.event_type}'"
            )

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a JSON-compatible dictionary.

        datetime is converted to ISO 8601 UTC string.
        """
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "store_id": self.store_id,
            "visitor_id": self.visitor_id,
            "timestamp": self.timestamp.isoformat(),
            "camera_id": self.camera_id,
            "attributes": self.attributes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Event:
        """Deserialise from a dictionary.

        Validates that all required fields are present and event_type is valid.
        """
        required_fields = {
            "event_id",
            "event_type",
            "store_id",
            "visitor_id",
            "timestamp",
            "camera_id",
        }
        missing = required_fields - set(data.keys())
        if missing:
            raise ValueError(f"Missing required fields: {sorted(missing)}")

        # Parse timestamp from ISO 8601 string
        ts = data["timestamp"]
        if isinstance(ts, str):
            # Handle both 'Z' suffix and '+00:00' offset
            ts_str = ts.replace("Z", "+00:00")
            parsed_ts = datetime.fromisoformat(ts_str)
        elif isinstance(ts, datetime):
            parsed_ts = ts
        else:
            raise ValueError(
                f"timestamp must be an ISO 8601 string or datetime, got {type(ts)}"
            )

        # Ensure timezone-aware (UTC)
        if parsed_ts.tzinfo is None:
            parsed_ts = parsed_ts.replace(tzinfo=timezone.utc)

        return cls(
            event_id=data["event_id"],
            event_type=data["event_type"],
            store_id=data["store_id"],
            visitor_id=data["visitor_id"],
            timestamp=parsed_ts,
            camera_id=data["camera_id"],
            attributes=data.get("attributes", {}),
        )
