"""
Anomaly detector: identifies operational anomalies from event stream state.

Detects:
- Queue buildup (depth > 5 for > 180s)
- Empty store (0 visitors for > 600s during operating hours)
- Unusual dwell (> 900s in a single zone)
- Camera overlap conflict (same track in non-adjacent zones within 2s)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Anomaly:
    """Represents a detected anomaly.

    Attributes:
        anomaly_type: Type identifier (e.g. QUEUE_BUILDUP, EMPTY_STORE).
        severity: One of "high", "medium", "low".
        detected_at: Timestamp when the anomaly was detected.
        description: Human-readable description.
        metadata: Additional context (zone_id, visitor_id, etc.).
    """

    anomaly_type: str
    severity: str
    detected_at: datetime
    description: str
    metadata: dict[str, Any] = field(default_factory=dict)


class AnomalyDetector:
    """Detects operational anomalies based on current system state.

    Each check method returns an Anomaly if the threshold is exceeded,
    or None if within normal parameters.
    """

    # Thresholds
    QUEUE_DEPTH_THRESHOLD: int = 5
    QUEUE_DURATION_THRESHOLD: float = 180.0  # seconds
    EMPTY_STORE_DURATION_THRESHOLD: float = 600.0  # seconds
    UNUSUAL_DWELL_THRESHOLD: float = 900.0  # seconds
    CAMERA_OVERLAP_GAP_THRESHOLD: float = 2.0  # seconds

    def check_queue_buildup(
        self, depth: int, duration_seconds: float, zone_id: str
    ) -> Anomaly | None:
        """Check for queue buildup anomaly.

        Triggers when depth > 5 for > 180s.

        Args:
            depth: Current queue depth.
            duration_seconds: How long the queue has been at this depth.
            zone_id: The queue zone identifier.

        Returns:
            Anomaly with severity "high" if triggered, None otherwise.
        """
        if depth > self.QUEUE_DEPTH_THRESHOLD and duration_seconds > self.QUEUE_DURATION_THRESHOLD:
            return Anomaly(
                anomaly_type="QUEUE_BUILDUP",
                severity="high",
                detected_at=datetime.utcnow(),
                description=(
                    f"Queue depth {depth} in {zone_id} "
                    f"sustained for {duration_seconds:.0f}s"
                ),
                metadata={
                    "zone_id": zone_id,
                    "depth": depth,
                    "duration_seconds": duration_seconds,
                },
            )
        return None

    def check_empty_store(
        self, visitor_count: int, duration_seconds: float
    ) -> Anomaly | None:
        """Check for empty store anomaly.

        Triggers when visitor_count == 0 for > 600s during operating hours.

        Args:
            visitor_count: Current number of visitors in the store.
            duration_seconds: How long the store has been empty.

        Returns:
            Anomaly with severity "medium" if triggered, None otherwise.
        """
        if visitor_count == 0 and duration_seconds > self.EMPTY_STORE_DURATION_THRESHOLD:
            return Anomaly(
                anomaly_type="EMPTY_STORE",
                severity="medium",
                detected_at=datetime.utcnow(),
                description=(
                    f"Store empty for {duration_seconds:.0f}s during operating hours"
                ),
                metadata={
                    "visitor_count": visitor_count,
                    "duration_seconds": duration_seconds,
                },
            )
        return None

    def check_unusual_dwell(
        self, visitor_id: str, zone_id: str, dwell_seconds: float
    ) -> Anomaly | None:
        """Check for unusual dwell time anomaly.

        Triggers when dwell_seconds > 900.

        Args:
            visitor_id: The visitor with unusual dwell.
            zone_id: The zone they're dwelling in.
            dwell_seconds: How long they've been in the zone.

        Returns:
            Anomaly with severity "low" if triggered, None otherwise.
        """
        if dwell_seconds > self.UNUSUAL_DWELL_THRESHOLD:
            return Anomaly(
                anomaly_type="UNUSUAL_DWELL",
                severity="low",
                detected_at=datetime.utcnow(),
                description=(
                    f"Visitor {visitor_id} in {zone_id} "
                    f"for {dwell_seconds:.0f}s (threshold: 900s)"
                ),
                metadata={
                    "visitor_id": visitor_id,
                    "zone_id": zone_id,
                    "dwell_seconds": dwell_seconds,
                },
            )
        return None

    def check_camera_overlap(
        self,
        track_id: int,
        zone_a: str,
        zone_b: str,
        gap_seconds: float,
        adjacency_map: dict[str, list[str]],
    ) -> Anomaly | None:
        """Check for camera overlap conflict.

        Triggers when same track appears in two non-adjacent zones within 2s.

        Args:
            track_id: The track that appeared in both zones.
            zone_a: First zone.
            zone_b: Second zone.
            gap_seconds: Time gap between detections in the two zones.
            adjacency_map: Dict mapping zone_id → list of adjacent zone_ids.

        Returns:
            Anomaly with severity "high" if triggered, None otherwise.
        """
        if gap_seconds > self.CAMERA_OVERLAP_GAP_THRESHOLD:
            return None

        # Check if zones are adjacent
        adjacent_to_a = adjacency_map.get(zone_a, [])
        if zone_b in adjacent_to_a:
            return None  # Adjacent zones — not an anomaly

        return Anomaly(
            anomaly_type="CAMERA_OVERLAP_CONFLICT",
            severity="high",
            detected_at=datetime.utcnow(),
            description=(
                f"Track {track_id} detected in non-adjacent zones "
                f"{zone_a} and {zone_b} within {gap_seconds:.1f}s"
            ),
            metadata={
                "track_id": track_id,
                "zone_a": zone_a,
                "zone_b": zone_b,
                "gap_seconds": gap_seconds,
            },
        )
