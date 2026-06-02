"""
Event engine orchestrator.

Consumes TrackFrame objects from the detection pipeline, applies business
logic (visitor registry, zone tracking, queue tracking), and emits
canonical Event objects onto the event queue.
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from shapely.geometry import Point, Polygon

from detection.models import TrackDetection, TrackFrame
from engine.anomaly_detector import AnomalyDetector
from engine.models import Event
from engine.queue_tracker import QueueTracker
from engine.visitor_registry import VisitorRegistry
from engine.zone_tracker import ZoneTracker

logger = logging.getLogger(__name__)


class EventEngine:
    """Orchestrates event generation from detection pipeline output.

    Consumes TrackFrame from track_queue, applies:
    - VisitorRegistry for stable visitor_id assignment
    - Entry/exit boundary crossing detection
    - ZoneTracker for zone occupancy and dwell
    - QueueTracker for billing queue monitoring

    Emits Event objects onto event_queue.

    Args:
        track_queue: Input queue of TrackFrame objects from DetectionPipeline.
        event_queue: Output queue for emitted Event objects.
        store_layout: Store configuration dict with keys:
            - store_id: str
            - entry_zone: dict with "polygon" key (list of (x,y) tuples)
            - exit_zone: dict with "polygon" key
            - zones: list of zone dicts with "zone_id" and "polygon"
            - queue_zone: dict with "zone_id" and "polygon"
            - adjacency_map: dict[str, list[str]]
    """

    # Time to wait before confirming an EXIT (to avoid false exits from occlusion)
    EXIT_CONFIRMATION_SECONDS: float = 60.0
    # Re-entry threshold
    REENTRY_THRESHOLD_SECONDS: float = 300.0

    def __init__(
        self,
        track_queue: asyncio.Queue,
        event_queue: asyncio.Queue,
        store_layout: dict[str, Any],
    ) -> None:
        self._track_queue = track_queue
        self._event_queue = event_queue
        self._store_layout = store_layout

        self._store_id: str = store_layout.get("store_id", "store-default")

        # Parse entry/exit polygons
        entry_zone = store_layout.get("entry_zone", {})
        exit_zone = store_layout.get("exit_zone", {})
        self._entry_polygon: Polygon | None = (
            Polygon(entry_zone["polygon"]) if entry_zone.get("polygon") else None
        )
        self._exit_polygon: Polygon | None = (
            Polygon(exit_zone["polygon"]) if exit_zone.get("polygon") else None
        )

        # Parse floor zones
        self._zones: list[dict[str, Any]] = store_layout.get("zones", [])

        # Parse queue zone
        self._queue_zone: dict[str, Any] | None = store_layout.get("queue_zone")
        self._queue_polygon: Polygon | None = None
        if self._queue_zone and self._queue_zone.get("polygon"):
            self._queue_polygon = Polygon(self._queue_zone["polygon"])

        # Adjacency map for overlap detection
        self._adjacency_map: dict[str, list[str]] = store_layout.get(
            "adjacency_map", {}
        )

        # Sub-components
        self._visitor_registry = VisitorRegistry()
        self._zone_tracker = ZoneTracker(self._store_id, "MULTI")
        self._queue_tracker = QueueTracker(self._store_id, "CAM1")
        self._anomaly_detector = AnomalyDetector()

        # State tracking
        # track_id → whether they were inside entry zone on previous frame
        self._prev_in_entry: dict[int, bool] = {}
        # track_id → whether they were inside exit zone on previous frame
        self._prev_in_exit: dict[int, bool] = {}
        # track_id → whether they were inside queue zone on previous frame
        self._prev_in_queue: dict[int, bool] = {}
        # visitor_id → set of tracks that have entered (to avoid duplicate ENTRY)
        self._entered_visitors: set[str] = set()
        # Pending exits: visitor_id → (timestamp, track_id) — confirmed after 60s
        self._pending_exits: dict[str, tuple[datetime, int]] = {}

        self._running: bool = False

    async def run(self) -> None:
        """Main event engine loop.

        Consumes TrackFrame from track_queue and emits Events to event_queue.
        """
        self._running = True
        logger.info("EventEngine started")

        try:
            while self._running:
                try:
                    track_frame: TrackFrame = await asyncio.wait_for(
                        self._track_queue.get(), timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue

                start_time = time.perf_counter()
                events = self._process_frame(track_frame)
                latency_ms = (time.perf_counter() - start_time) * 1000

                for event in events:
                    await self._event_queue.put(event)
                    logger.debug(
                        "Event emitted: type=%s visitor=%s store=%s latency=%.1fms",
                        event.event_type,
                        event.visitor_id,
                        event.store_id,
                        latency_ms,
                    )

        except asyncio.CancelledError:
            logger.info("EventEngine cancelled")
            raise
        finally:
            self._running = False
            logger.info("EventEngine stopped")

    def _process_frame(self, frame: TrackFrame) -> list[Event]:
        """Process a single TrackFrame and return emitted events."""
        events: list[Event] = []
        timestamp = frame.timestamp
        camera_id = frame.camera_id

        # Filter out staff detections — only process visitors
        visitor_detections = [
            d for d in frame.detections if d.role == "visitor"
        ]

        for detection in visitor_detections:
            det_events = self._process_detection(
                detection, timestamp, camera_id
            )
            events.extend(det_events)

        return events

    def _process_detection(
        self,
        detection: TrackDetection,
        timestamp: datetime,
        camera_id: str,
    ) -> list[Event]:
        """Process a single detection through all business logic."""
        events: list[Event] = []
        track_id = detection.track_id
        bbox = detection.bbox

        # Calculate centroid
        cx = (bbox[0] + bbox[2]) / 2.0
        cy = (bbox[1] + bbox[3]) / 2.0
        centroid = (cx, cy)
        point = Point(cx, cy)

        # --- Entry/Exit detection ---
        entry_events = self._check_entry_exit(
            track_id, point, timestamp, camera_id
        )
        events.extend(entry_events)

        # Get visitor_id (must have been assigned by entry detection or prior frame)
        visitor_id = self._visitor_registry.get_visitor_id(track_id)
        if visitor_id is None:
            # Assign if not yet known (e.g. first frame, no entry zone configured)
            visitor_id = self._visitor_registry.get_or_assign(track_id, timestamp)

        # --- Zone tracking ---
        zone_events = self._zone_tracker.update(
            visitor_id=visitor_id,
            bbox_centroid=centroid,
            timestamp=timestamp,
            zones=self._zones,
        )
        # Update camera_id on emitted zone events
        for evt in zone_events:
            evt.camera_id = camera_id
        events.extend(zone_events)

        # --- Queue tracking ---
        queue_events = self._check_queue(
            track_id, visitor_id, point, timestamp, camera_id
        )
        events.extend(queue_events)

        return events

    def _check_entry_exit(
        self,
        track_id: int,
        point: Point,
        timestamp: datetime,
        camera_id: str,
    ) -> list[Event]:
        """Detect entry/exit boundary crossings."""
        events: list[Event] = []

        # --- Entry detection ---
        if self._entry_polygon is not None:
            currently_in_entry = self._entry_polygon.contains(point)
            was_in_entry = self._prev_in_entry.get(track_id, False)

            if currently_in_entry and not was_in_entry:
                # Inward crossing — check if re-entry or new entry
                visitor_id = self._visitor_registry.get_visitor_id(track_id)

                if visitor_id is not None and visitor_id in self._entered_visitors:
                    # Already entered — could be re-entry after pending exit
                    if visitor_id in self._pending_exits:
                        exit_time, _ = self._pending_exits.pop(visitor_id)
                        gap = (timestamp - exit_time).total_seconds()
                        if gap < self.REENTRY_THRESHOLD_SECONDS:
                            # Re-entry
                            events.append(
                                Event(
                                    event_id=str(uuid.uuid4()),
                                    event_type="REENTRY",
                                    store_id=self._store_id,
                                    visitor_id=visitor_id,
                                    timestamp=timestamp,
                                    camera_id=camera_id,
                                    attributes={"gap_seconds": gap},
                                )
                            )
                else:
                    # New entry
                    visitor_id = self._visitor_registry.get_or_assign(
                        track_id, timestamp
                    )
                    self._entered_visitors.add(visitor_id)
                    events.append(
                        Event(
                            event_id=str(uuid.uuid4()),
                            event_type="ENTRY",
                            store_id=self._store_id,
                            visitor_id=visitor_id,
                            timestamp=timestamp,
                            camera_id=camera_id,
                            attributes={},
                        )
                    )

            self._prev_in_entry[track_id] = currently_in_entry

        # --- Exit detection ---
        if self._exit_polygon is not None:
            currently_in_exit = self._exit_polygon.contains(point)
            was_in_exit = self._prev_in_exit.get(track_id, False)

            if currently_in_exit and not was_in_exit:
                # Outward crossing
                visitor_id = self._visitor_registry.get_visitor_id(track_id)
                if visitor_id is not None:
                    self._visitor_registry.record_exit(visitor_id, timestamp)
                    self._pending_exits[visitor_id] = (timestamp, track_id)
                    events.append(
                        Event(
                            event_id=str(uuid.uuid4()),
                            event_type="EXIT",
                            store_id=self._store_id,
                            visitor_id=visitor_id,
                            timestamp=timestamp,
                            camera_id=camera_id,
                            attributes={},
                        )
                    )
                    # Emit ZONE_EXIT for any active zones on track loss
                    zone_exit_events = self._zone_tracker.update(
                        visitor_id=visitor_id,
                        bbox_centroid=(0, 0),
                        timestamp=timestamp,
                        zones=self._zones,
                        track_lost=True,
                    )
                    events.extend(zone_exit_events)

            self._prev_in_exit[track_id] = currently_in_exit

        return events

    def _check_queue(
        self,
        track_id: int,
        visitor_id: str,
        point: Point,
        timestamp: datetime,
        camera_id: str,
    ) -> list[Event]:
        """Detect queue zone entry/exit."""
        events: list[Event] = []

        if self._queue_polygon is None:
            return events

        currently_in_queue = self._queue_polygon.contains(point)
        was_in_queue = self._prev_in_queue.get(track_id, False)

        if currently_in_queue and not was_in_queue:
            # Entered queue zone
            event = self._queue_tracker.join(visitor_id, timestamp)
            event.camera_id = camera_id
            events.append(event)

        elif not currently_in_queue and was_in_queue:
            # Left queue zone — check for abandonment
            abandon_event = self._queue_tracker.check_abandon(
                visitor_id, timestamp, pos_transactions=[]
            )
            if abandon_event is not None:
                abandon_event.camera_id = camera_id
                events.append(abandon_event)

        self._prev_in_queue[track_id] = currently_in_queue

        return events

    def stop(self) -> None:
        """Signal the engine to stop."""
        self._running = False
