"""
Zone tracker: state machine for zone occupancy and dwell detection.

Tracks visitor presence within zones and emits ZONE_ENTER, ZONE_EXIT,
and ZONE_DWELL events based on polygon containment.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum, auto
from typing import Any

from shapely.geometry import Point, Polygon

from engine.models import Event


class ZoneState(Enum):
    """State machine states for visitor-zone relationship."""

    OUTSIDE = auto()
    IN_ZONE = auto()
    DWELL_EMITTED = auto()


class _VisitorZoneState:
    """Internal state for a single visitor in a single zone."""

    __slots__ = ("state", "enter_time", "dwell_emitted")

    def __init__(self) -> None:
        self.state: ZoneState = ZoneState.OUTSIDE
        self.enter_time: datetime | None = None
        self.dwell_emitted: bool = False


class ZoneTracker:
    """Tracks visitor zone occupancy using a per-visitor state machine.

    State transitions:
        OUTSIDE → IN_ZONE (emits ZONE_ENTER)
        IN_ZONE → DWELL_EMITTED (emits ZONE_DWELL when dwell >= 30s)
        IN_ZONE → OUTSIDE (emits ZONE_EXIT)
        DWELL_EMITTED → OUTSIDE (emits ZONE_EXIT)

    On track loss: emits ZONE_EXIT with accumulated dwell.
    """

    # Dwell threshold in seconds
    DWELL_THRESHOLD_SECONDS: float = 30.0

    def __init__(self, store_id: str, camera_id: str) -> None:
        """Initialise the zone tracker.

        Args:
            store_id: Store identifier for emitted events.
            camera_id: Camera identifier for emitted events.
        """
        self._store_id = store_id
        self._camera_id = camera_id
        # (visitor_id, zone_id) → _VisitorZoneState
        self._states: dict[tuple[str, str], _VisitorZoneState] = {}

    def update(
        self,
        visitor_id: str,
        bbox_centroid: tuple[float, float],
        timestamp: datetime,
        zones: list[dict[str, Any]],
        track_lost: bool = False,
    ) -> list[Event]:
        """Update zone state for a visitor and emit events.

        Args:
            visitor_id: Stable visitor identifier.
            bbox_centroid: (x, y) normalised centroid of the bounding box.
            timestamp: Current timestamp.
            zones: List of zone dicts with keys:
                - zone_id: str
                - polygon: list of (x, y) tuples (normalised coordinates)
            track_lost: If True, emit ZONE_EXIT for all active zones.

        Returns:
            List of emitted Event objects.
        """
        events: list[Event] = []

        if track_lost:
            events.extend(self._handle_track_loss(visitor_id, timestamp))
            return events

        point = Point(bbox_centroid[0], bbox_centroid[1])

        for zone in zones:
            zone_id = zone["zone_id"]
            polygon = Polygon(zone["polygon"])
            key = (visitor_id, zone_id)

            state = self._states.get(key)
            if state is None:
                state = _VisitorZoneState()
                self._states[key] = state

            inside = polygon.contains(point)

            if state.state == ZoneState.OUTSIDE:
                if inside:
                    # Transition: OUTSIDE → IN_ZONE
                    state.state = ZoneState.IN_ZONE
                    state.enter_time = timestamp
                    state.dwell_emitted = False
                    events.append(
                        Event(
                            event_id=str(uuid.uuid4()),
                            event_type="ZONE_ENTER",
                            store_id=self._store_id,
                            visitor_id=visitor_id,
                            timestamp=timestamp,
                            camera_id=self._camera_id,
                            attributes={"zone_id": zone_id},
                        )
                    )

            elif state.state == ZoneState.IN_ZONE:
                if inside:
                    # Check if dwell threshold reached
                    dwell = (timestamp - state.enter_time).total_seconds()
                    if dwell >= self.DWELL_THRESHOLD_SECONDS:
                        # Transition: IN_ZONE → DWELL_EMITTED
                        state.state = ZoneState.DWELL_EMITTED
                        state.dwell_emitted = True
                        events.append(
                            Event(
                                event_id=str(uuid.uuid4()),
                                event_type="ZONE_DWELL",
                                store_id=self._store_id,
                                visitor_id=visitor_id,
                                timestamp=timestamp,
                                camera_id=self._camera_id,
                                attributes={
                                    "zone_id": zone_id,
                                    "dwell_seconds": dwell,
                                },
                            )
                        )
                else:
                    # Transition: IN_ZONE → OUTSIDE
                    dwell = (timestamp - state.enter_time).total_seconds()
                    state.state = ZoneState.OUTSIDE
                    events.append(
                        Event(
                            event_id=str(uuid.uuid4()),
                            event_type="ZONE_EXIT",
                            store_id=self._store_id,
                            visitor_id=visitor_id,
                            timestamp=timestamp,
                            camera_id=self._camera_id,
                            attributes={
                                "zone_id": zone_id,
                                "dwell_seconds": dwell,
                            },
                        )
                    )

            elif state.state == ZoneState.DWELL_EMITTED:
                if not inside:
                    # Transition: DWELL_EMITTED → OUTSIDE
                    dwell = (timestamp - state.enter_time).total_seconds()
                    state.state = ZoneState.OUTSIDE
                    events.append(
                        Event(
                            event_id=str(uuid.uuid4()),
                            event_type="ZONE_EXIT",
                            store_id=self._store_id,
                            visitor_id=visitor_id,
                            timestamp=timestamp,
                            camera_id=self._camera_id,
                            attributes={
                                "zone_id": zone_id,
                                "dwell_seconds": dwell,
                            },
                        )
                    )

        return events

    def _handle_track_loss(
        self, visitor_id: str, timestamp: datetime
    ) -> list[Event]:
        """Emit ZONE_EXIT for all zones the visitor is currently in.

        Args:
            visitor_id: The visitor whose track was lost.
            timestamp: Last known timestamp.

        Returns:
            List of ZONE_EXIT events.
        """
        events: list[Event] = []
        keys_to_reset = []

        for key, state in self._states.items():
            vid, zone_id = key
            if vid != visitor_id:
                continue
            if state.state in (ZoneState.IN_ZONE, ZoneState.DWELL_EMITTED):
                dwell = (timestamp - state.enter_time).total_seconds()
                events.append(
                    Event(
                        event_id=str(uuid.uuid4()),
                        event_type="ZONE_EXIT",
                        store_id=self._store_id,
                        visitor_id=visitor_id,
                        timestamp=timestamp,
                        camera_id=self._camera_id,
                        attributes={
                            "zone_id": zone_id,
                            "dwell_seconds": dwell,
                        },
                    )
                )
                keys_to_reset.append(key)

        for key in keys_to_reset:
            self._states[key].state = ZoneState.OUTSIDE

        return events
