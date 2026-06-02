"""
Event engine orchestrator — Phase 9: AnomalyDetector integrated.

Consumes TrackFrame objects from the detection pipeline, applies business
logic, and emits Events and Anomalies onto the event queue.
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
from engine.anomaly_detector import Anomaly, AnomalyDetector
from engine.models import Event
from engine.queue_tracker import QueueTracker
from engine.visitor_registry import VisitorRegistry
from engine.zone_tracker import ZoneTracker

logger = logging.getLogger(__name__)


class EventEngine:
    """Orchestrates event generation from detection pipeline output."""

    EXIT_CONFIRMATION_SECONDS: float = 60.0
    REENTRY_THRESHOLD_SECONDS: float = 300.0
    # Minimum seconds between repeated anomaly emissions of the same type
    ANOMALY_COOLDOWN_SECONDS: float = 300.0

    def __init__(
        self,
        track_queue: asyncio.Queue,
        event_queue: asyncio.Queue,
        store_layout: dict[str, Any],
        db=None,
    ) -> None:
        self._track_queue = track_queue
        self._event_queue = event_queue
        self._store_layout = store_layout
        self._db = db

        self._store_id: str = store_layout.get("store_id", "store-default")

        entry_zone = store_layout.get("entry_zone", {})
        exit_zone = store_layout.get("exit_zone", {})
        self._entry_polygon: Polygon | None = (
            Polygon(entry_zone["polygon"]) if entry_zone.get("polygon") else None
        )
        self._exit_polygon: Polygon | None = (
            Polygon(exit_zone["polygon"]) if exit_zone.get("polygon") else None
        )

        self._zones: list[dict[str, Any]] = store_layout.get("zones", [])
        self._queue_zone: dict[str, Any] | None = store_layout.get("queue_zone")
        self._queue_polygon: Polygon | None = None
        if self._queue_zone and self._queue_zone.get("polygon"):
            self._queue_polygon = Polygon(self._queue_zone["polygon"])

        self._adjacency_map: dict[str, list[str]] = store_layout.get("adjacency_map", {})

        self._visitor_registry = VisitorRegistry()
        self._zone_tracker = ZoneTracker(self._store_id, "MULTI")
        self._queue_tracker = QueueTracker(self._store_id, "CAM1")
        self._anomaly_detector = AnomalyDetector()

        # Entry/exit/queue state
        self._prev_in_entry: dict[int, bool] = {}
        self._prev_in_exit: dict[int, bool] = {}
        self._prev_in_queue: dict[int, bool] = {}
        self._entered_visitors: set[str] = set()
        self._pending_exits: dict[str, tuple[datetime, int]] = {}

        # Phase 9.1: Queue buildup — zone_id → time depth first exceeded threshold
        self._queue_buildup_since: dict[str, datetime] = {}

        # Phase 9.1: Empty store — timestamp when visitor count first hit 0
        self._empty_store_since: datetime | None = None

        # Phase 9.1: Dwell anomaly tracking — (visitor_id, zone_id) → enter_time
        self._zone_enter_times: dict[tuple[str, str], datetime] = {}
        self._unusual_dwell_alerted: set[tuple[str, str]] = set()

        # Phase 9.3: Camera overlap — track_id → [(zone_id, timestamp, confidence)]
        self._recent_positions: dict[int, list[tuple[str, datetime, float]]] = {}

        # Anomaly cooldown — key → last emitted timestamp
        self._last_anomaly_at: dict[str, datetime] = {}

        self._running: bool = False

    def set_db(self, db) -> None:
        """Set the database instance after construction."""
        self._db = db

    async def run(self) -> None:
        """Main event engine loop with anomaly detection."""
        self._running = True
        logger.info("EventEngine started")

        try:
            while self._running:
                try:
                    track_frame: TrackFrame = await asyncio.wait_for(
                        self._track_queue.get(), timeout=1.0
                    )
                except asyncio.TimeoutError:
                    # Still run empty-store check
                    await self._run_anomaly_checks([], datetime.now(timezone.utc))
                    continue

                start_time = time.perf_counter()
                events = self._process_frame(track_frame)
                latency_ms = (time.perf_counter() - start_time) * 1000

                for event in events:
                    await self._event_queue.put(event)
                    logger.debug(
                        "Event emitted: type=%s visitor=%s store=%s latency=%.1fms",
                        event.event_type, event.visitor_id, event.store_id, latency_ms,
                    )

                # Phase 9.1: Run anomaly checks after every frame
                await self._run_anomaly_checks(
                    track_frame.detections, track_frame.timestamp
                )

        except asyncio.CancelledError:
            logger.info("EventEngine cancelled")
            raise
        finally:
            self._running = False
            logger.info("EventEngine stopped")

    # ------------------------------------------------------------------
    # Phase 9.1 — Anomaly checks
    # ------------------------------------------------------------------

    async def _run_anomaly_checks(
        self, detections: list[TrackDetection], timestamp: datetime
    ) -> None:
        """Run all anomaly checks and persist/broadcast any that trigger."""
        anomalies: list[Anomaly] = []

        # 1. Queue buildup
        if self._queue_zone:
            qzone_id = self._queue_zone.get("zone_id", "ZONE_QUEUE")
            depth = self._queue_tracker.get_depth()
            if depth > self._anomaly_detector.QUEUE_DEPTH_THRESHOLD:
                if qzone_id not in self._queue_buildup_since:
                    self._queue_buildup_since[qzone_id] = timestamp
                duration = (timestamp - self._queue_buildup_since[qzone_id]).total_seconds()
                a = self._anomaly_detector.check_queue_buildup(depth, duration, qzone_id)
                if a and self._should_emit(f"QUEUE_BUILDUP:{qzone_id}", timestamp):
                    anomalies.append(a)
            else:
                self._queue_buildup_since.pop(qzone_id, None)

        # 2. Empty store
        visitor_count = len([d for d in detections if d.role == "visitor"])
        if visitor_count == 0:
            if self._empty_store_since is None:
                self._empty_store_since = timestamp
            duration = (timestamp - self._empty_store_since).total_seconds()
            a = self._anomaly_detector.check_empty_store(0, duration)
            if a and self._should_emit("EMPTY_STORE:", timestamp):
                anomalies.append(a)
        else:
            self._empty_store_since = None

        # 3. Unusual dwell — check all tracked zone enter times
        for (visitor_id, zone_id), enter_time in list(self._zone_enter_times.items()):
            dwell = (timestamp - enter_time).total_seconds()
            key = (visitor_id, zone_id)
            if key not in self._unusual_dwell_alerted:
                a = self._anomaly_detector.check_unusual_dwell(visitor_id, zone_id, dwell)
                if a and self._should_emit(f"UNUSUAL_DWELL:{visitor_id}:{zone_id}", timestamp):
                    anomalies.append(a)
                    self._unusual_dwell_alerted.add(key)

        for anomaly in anomalies:
            await self._emit_anomaly(anomaly)

    async def _emit_anomaly(self, anomaly: Anomaly) -> None:
        """Persist anomaly to DB and broadcast via event_queue."""
        logger.info(
            "Anomaly: type=%s severity=%s store=%s desc=%s",
            anomaly.anomaly_type, anomaly.severity, self._store_id,
            anomaly.description[:60],
        )
        if self._db is not None:
            try:
                await self._db.insert_anomaly(anomaly, self._store_id)
            except Exception as exc:
                logger.warning("Failed to persist anomaly %s: %s", anomaly.anomaly_type, exc)

        # Broadcast as event for WebSocket clients
        broadcast_event = Event(
            event_id=str(uuid.uuid4()),
            event_type="ZONE_DWELL",
            store_id=self._store_id,
            visitor_id="system",
            timestamp=anomaly.detected_at,
            camera_id="SYSTEM",
            attributes={
                "anomaly_type": anomaly.anomaly_type,
                "severity": anomaly.severity,
                "description": anomaly.description,
                **anomaly.metadata,
            },
        )
        await self._event_queue.put(broadcast_event)

    def _should_emit(self, key: str, now: datetime) -> bool:
        """True if cooldown has elapsed since last emission of this anomaly key."""
        last = self._last_anomaly_at.get(key)
        if last is None or (now - last).total_seconds() >= self.ANOMALY_COOLDOWN_SECONDS:
            self._last_anomaly_at[key] = now
            return True
        return False

    # ------------------------------------------------------------------
    # Phase 9.3 — Camera overlap conflict detection
    # ------------------------------------------------------------------

    def _check_camera_overlap(
        self,
        track_id: int,
        zone_id: str,
        timestamp: datetime,
        confidence: float,
    ) -> Anomaly | None:
        """Detect same track in two non-adjacent zones within 2s.

        Uses higher-confidence detection as authoritative position.
        Tie-breaks on earlier timestamp.
        """
        positions = self._recent_positions.setdefault(track_id, [])
        positions.append((zone_id, timestamp, confidence))

        # Prune to 2s window
        cutoff = timestamp.timestamp() - self._anomaly_detector.CAMERA_OVERLAP_GAP_THRESHOLD
        positions[:] = [(z, t, c) for z, t, c in positions if t.timestamp() >= cutoff]

        # Collect distinct zones seen in window
        seen: dict[str, tuple[datetime, float]] = {}
        for z, t, c in positions:
            if z not in seen or c > seen[z][1] or (c == seen[z][1] and t < seen[z][0]):
                seen[z] = (t, c)

        if len(seen) < 2:
            return None

        zone_list = list(seen.keys())
        for i in range(len(zone_list)):
            for j in range(i + 1, len(zone_list)):
                zone_a, zone_b = zone_list[i], zone_list[j]
                t_a, c_a = seen[zone_a]
                t_b, c_b = seen[zone_b]
                gap = abs((t_a - t_b).total_seconds())
                anomaly = self._anomaly_detector.check_camera_overlap(
                    track_id, zone_a, zone_b, gap, self._adjacency_map
                )
                if anomaly:
                    return anomaly
        return None

    # ------------------------------------------------------------------
    # Frame processing
    # ------------------------------------------------------------------

    def _process_frame(self, frame: TrackFrame) -> list[Event]:
        """Process a single TrackFrame and return emitted events."""
        events: list[Event] = []
        for detection in frame.detections:
            if detection.role != "visitor":
                continue
            det_events = self._process_detection(
                detection, frame.timestamp, frame.camera_id
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
        confidence = detection.confidence

        cx = (bbox[0] + bbox[2]) / 2.0
        cy = (bbox[1] + bbox[3]) / 2.0
        centroid = (cx, cy)
        point = Point(cx, cy)

        events.extend(self._check_entry_exit(track_id, point, timestamp, camera_id))

        visitor_id = self._visitor_registry.get_visitor_id(track_id)
        if visitor_id is None:
            visitor_id = self._visitor_registry.get_or_assign(track_id, timestamp)

        zone_events = self._zone_tracker.update(
            visitor_id=visitor_id,
            bbox_centroid=centroid,
            timestamp=timestamp,
            zones=self._zones,
        )
        for evt in zone_events:
            evt.camera_id = camera_id
            # Track dwell entry/exit times for UNUSUAL_DWELL (9.1)
            if evt.event_type == "ZONE_ENTER":
                self._zone_enter_times[(visitor_id, evt.attributes.get("zone_id", ""))] = timestamp
            elif evt.event_type in ("ZONE_EXIT", "ZONE_DWELL"):
                z = evt.attributes.get("zone_id", "")
                self._zone_enter_times.pop((visitor_id, z), None)
                self._unusual_dwell_alerted.discard((visitor_id, z))
        events.extend(zone_events)

        # Phase 9.3: camera overlap check for each zone the centroid is inside
        for zone in self._zones:
            z_poly = Polygon(zone["polygon"])
            if z_poly.contains(point):
                overlap_anomaly = self._check_camera_overlap(
                    track_id, zone["zone_id"], timestamp, confidence
                )
                if overlap_anomaly and self._should_emit(
                    f"CAMERA_OVERLAP:{track_id}", timestamp
                ):
                    asyncio.ensure_future(self._emit_anomaly(overlap_anomaly))

        events.extend(self._check_queue(track_id, visitor_id, point, timestamp, camera_id))
        return events

    def _check_entry_exit(
        self, track_id: int, point: Point, timestamp: datetime, camera_id: str
    ) -> list[Event]:
        events: list[Event] = []

        if self._entry_polygon is not None:
            in_entry = self._entry_polygon.contains(point)
            was = self._prev_in_entry.get(track_id, False)
            if in_entry and not was:
                visitor_id = self._visitor_registry.get_visitor_id(track_id)
                if visitor_id is not None and visitor_id in self._entered_visitors:
                    if visitor_id in self._pending_exits:
                        exit_time, _ = self._pending_exits.pop(visitor_id)
                        gap = (timestamp - exit_time).total_seconds()
                        if gap < self.REENTRY_THRESHOLD_SECONDS:
                            events.append(Event(
                                event_id=str(uuid.uuid4()), event_type="REENTRY",
                                store_id=self._store_id, visitor_id=visitor_id,
                                timestamp=timestamp, camera_id=camera_id,
                                attributes={"gap_seconds": gap},
                            ))
                else:
                    visitor_id = self._visitor_registry.get_or_assign(track_id, timestamp)
                    self._entered_visitors.add(visitor_id)
                    events.append(Event(
                        event_id=str(uuid.uuid4()), event_type="ENTRY",
                        store_id=self._store_id, visitor_id=visitor_id,
                        timestamp=timestamp, camera_id=camera_id, attributes={},
                    ))
            self._prev_in_entry[track_id] = in_entry

        if self._exit_polygon is not None:
            in_exit = self._exit_polygon.contains(point)
            was = self._prev_in_exit.get(track_id, False)
            if in_exit and not was:
                visitor_id = self._visitor_registry.get_visitor_id(track_id)
                if visitor_id is not None:
                    self._visitor_registry.record_exit(visitor_id, timestamp)
                    self._pending_exits[visitor_id] = (timestamp, track_id)
                    events.append(Event(
                        event_id=str(uuid.uuid4()), event_type="EXIT",
                        store_id=self._store_id, visitor_id=visitor_id,
                        timestamp=timestamp, camera_id=camera_id, attributes={},
                    ))
                    for ze in self._zone_tracker.update(
                        visitor_id=visitor_id, bbox_centroid=(0, 0),
                        timestamp=timestamp, zones=self._zones, track_lost=True,
                    ):
                        events.append(ze)
            self._prev_in_exit[track_id] = in_exit

        return events

    def _check_queue(
        self, track_id: int, visitor_id: str, point: Point,
        timestamp: datetime, camera_id: str,
    ) -> list[Event]:
        events: list[Event] = []
        if self._queue_polygon is None:
            return events

        in_queue = self._queue_polygon.contains(point)
        was = self._prev_in_queue.get(track_id, False)

        if in_queue and not was:
            evt = self._queue_tracker.join(visitor_id, timestamp)
            evt.camera_id = camera_id
            events.append(evt)
        elif not in_queue and was:
            abandon = self._queue_tracker.check_abandon(visitor_id, timestamp, [])
            if abandon:
                abandon.camera_id = camera_id
                events.append(abandon)

        self._prev_in_queue[track_id] = in_queue
        return events

    def stop(self) -> None:
        """Signal the engine to stop."""
        self._running = False
