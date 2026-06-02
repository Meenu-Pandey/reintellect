"""
Unit tests for EventEngine classification logic.

One test per event type (8 tests): ENTRY, EXIT, ZONE_ENTER, ZONE_EXIT,
ZONE_DWELL, BILLING_QUEUE_JOIN, BILLING_QUEUE_ABANDON, REENTRY.

Each test constructs a minimal TrackFrame sequence and asserts the correct
event type is emitted. No external I/O — uses in-memory queues.
"""

import asyncio
from datetime import datetime, timedelta, timezone

import pytest

from detection.models import TrackDetection, TrackFrame
from engine.event_engine import EventEngine


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

# Store layout with entry, exit, floor zones, and queue zone.
# All polygons use normalised [0,1] coordinates.
STORE_LAYOUT = {
    "store_id": "test-store",
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
    ],
    "queue_zone": {
        "zone_id": "ZONE_QUEUE",
        "polygon": [(0.7, 0.0), (1.0, 0.0), (1.0, 0.3), (0.7, 0.3)],
    },
    "adjacency_map": {},
}

BASE_TIME = datetime(2025, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


def _make_frame(
    track_id: int,
    bbox: tuple[float, float, float, float],
    timestamp: datetime,
    camera_id: str = "CAM3",
) -> TrackFrame:
    """Helper: create a TrackFrame with a single visitor detection."""
    return TrackFrame(
        camera_id=camera_id,
        frame_id=1,
        timestamp=timestamp,
        detections=[
            TrackDetection(
                track_id=track_id,
                bbox=bbox,
                confidence=0.9,
                role="visitor",
            )
        ],
    )


def _create_engine() -> tuple[EventEngine, asyncio.Queue, asyncio.Queue]:
    """Create an EventEngine with in-memory queues."""
    track_queue = asyncio.Queue()
    event_queue = asyncio.Queue()
    engine = EventEngine(track_queue, event_queue, STORE_LAYOUT)
    return engine, track_queue, event_queue


def _collect_events(engine: EventEngine, frame: TrackFrame) -> list:
    """Process a frame through the engine and return emitted events."""
    return engine._process_frame(frame)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_entry_event():
    """ENTRY event emitted when centroid crosses into entry zone."""
    engine, _, _ = _create_engine()

    # Centroid at (0.1, 0.1) — inside entry zone
    bbox = (0.05, 0.05, 0.15, 0.15)
    frame = _make_frame(track_id=1, bbox=bbox, timestamp=BASE_TIME)
    events = _collect_events(engine, frame)

    entry_events = [e for e in events if e.event_type == "ENTRY"]
    assert len(entry_events) == 1
    assert entry_events[0].store_id == "test-store"
    assert entry_events[0].visitor_id is not None


def test_exit_event():
    """EXIT event emitted when centroid crosses into exit zone."""
    engine, _, _ = _create_engine()

    # First: enter the store
    bbox_entry = (0.05, 0.05, 0.15, 0.15)
    frame_entry = _make_frame(track_id=1, bbox=bbox_entry, timestamp=BASE_TIME)
    _collect_events(engine, frame_entry)

    # Move to middle (clear entry zone state)
    bbox_mid = (0.4, 0.4, 0.5, 0.5)
    frame_mid = _make_frame(
        track_id=1, bbox=bbox_mid, timestamp=BASE_TIME + timedelta(seconds=10)
    )
    _collect_events(engine, frame_mid)

    # Cross into exit zone — centroid at (0.9, 0.9)
    bbox_exit = (0.85, 0.85, 0.95, 0.95)
    frame_exit = _make_frame(
        track_id=1, bbox=bbox_exit, timestamp=BASE_TIME + timedelta(seconds=20)
    )
    events = _collect_events(engine, frame_exit)

    exit_events = [e for e in events if e.event_type == "EXIT"]
    assert len(exit_events) == 1


def test_zone_enter_event():
    """ZONE_ENTER event emitted when centroid enters a floor zone."""
    engine, _, _ = _create_engine()

    # Enter store first
    bbox_entry = (0.05, 0.05, 0.15, 0.15)
    _collect_events(engine, _make_frame(1, bbox_entry, BASE_TIME))

    # Move into makeup zone — centroid at (0.45, 0.45)
    bbox_zone = (0.4, 0.4, 0.5, 0.5)
    frame = _make_frame(1, bbox_zone, BASE_TIME + timedelta(seconds=5))
    events = _collect_events(engine, frame)

    zone_enter = [e for e in events if e.event_type == "ZONE_ENTER"]
    assert len(zone_enter) == 1
    assert zone_enter[0].attributes["zone_id"] == "ZONE_MAKEUP"


def test_zone_exit_event():
    """ZONE_EXIT event emitted when centroid leaves a floor zone."""
    engine, _, _ = _create_engine()

    # Enter store
    _collect_events(engine, _make_frame(1, (0.05, 0.05, 0.15, 0.15), BASE_TIME))

    # Enter makeup zone
    _collect_events(
        engine, _make_frame(1, (0.4, 0.4, 0.5, 0.5), BASE_TIME + timedelta(seconds=5))
    )

    # Leave makeup zone — centroid at (0.1, 0.5), outside zone polygon
    bbox_outside = (0.05, 0.45, 0.15, 0.55)
    events = _collect_events(
        engine, _make_frame(1, bbox_outside, BASE_TIME + timedelta(seconds=10))
    )

    zone_exit = [e for e in events if e.event_type == "ZONE_EXIT"]
    assert len(zone_exit) == 1
    assert zone_exit[0].attributes["zone_id"] == "ZONE_MAKEUP"
    assert zone_exit[0].attributes["dwell_seconds"] >= 0


def test_zone_dwell_event():
    """ZONE_DWELL event emitted after >= 30s continuous presence in zone."""
    engine, _, _ = _create_engine()

    # Enter store
    _collect_events(engine, _make_frame(1, (0.05, 0.05, 0.15, 0.15), BASE_TIME))

    # Enter makeup zone
    _collect_events(
        engine, _make_frame(1, (0.4, 0.4, 0.5, 0.5), BASE_TIME + timedelta(seconds=5))
    )

    # Stay in zone for 30s
    events = _collect_events(
        engine, _make_frame(1, (0.4, 0.4, 0.5, 0.5), BASE_TIME + timedelta(seconds=35))
    )

    dwell_events = [e for e in events if e.event_type == "ZONE_DWELL"]
    assert len(dwell_events) == 1
    assert dwell_events[0].attributes["dwell_seconds"] >= 30.0


def test_billing_queue_join_event():
    """BILLING_QUEUE_JOIN emitted when centroid enters queue zone."""
    engine, _, _ = _create_engine()

    # Enter store
    _collect_events(engine, _make_frame(1, (0.05, 0.05, 0.15, 0.15), BASE_TIME))

    # Move to queue zone — centroid at (0.85, 0.15)
    bbox_queue = (0.8, 0.1, 0.9, 0.2)
    events = _collect_events(
        engine, _make_frame(1, bbox_queue, BASE_TIME + timedelta(seconds=60))
    )

    join_events = [e for e in events if e.event_type == "BILLING_QUEUE_JOIN"]
    assert len(join_events) == 1
    assert join_events[0].attributes["queue_position"] == 1


def test_billing_queue_abandon_event():
    """BILLING_QUEUE_ABANDON emitted when visitor leaves queue with no POS."""
    engine, _, _ = _create_engine()

    # Enter store
    _collect_events(engine, _make_frame(1, (0.05, 0.05, 0.15, 0.15), BASE_TIME))

    # Enter queue zone
    bbox_queue = (0.8, 0.1, 0.9, 0.2)
    _collect_events(
        engine, _make_frame(1, bbox_queue, BASE_TIME + timedelta(seconds=60))
    )

    # Leave queue zone (no POS transaction)
    bbox_outside_queue = (0.4, 0.4, 0.5, 0.5)
    events = _collect_events(
        engine,
        _make_frame(1, bbox_outside_queue, BASE_TIME + timedelta(seconds=180)),
    )

    abandon_events = [e for e in events if e.event_type == "BILLING_QUEUE_ABANDON"]
    assert len(abandon_events) == 1
    assert abandon_events[0].attributes["wait_seconds"] > 0


def test_reentry_event():
    """REENTRY event emitted when visitor re-enters within 300s of exit."""
    engine, _, _ = _create_engine()

    # Enter store
    _collect_events(engine, _make_frame(1, (0.05, 0.05, 0.15, 0.15), BASE_TIME))

    # Move to middle
    _collect_events(
        engine, _make_frame(1, (0.4, 0.4, 0.5, 0.5), BASE_TIME + timedelta(seconds=5))
    )

    # Exit store
    _collect_events(
        engine,
        _make_frame(1, (0.85, 0.85, 0.95, 0.95), BASE_TIME + timedelta(seconds=30)),
    )

    # Re-enter within 300s with a new track_id (ByteTrack assigned new ID)
    # But the VisitorRegistry must handle this via handle_reentry in the full flow.
    # For this test, we simulate by having the same track re-appear in entry zone.
    # First move out of exit zone
    _collect_events(
        engine,
        _make_frame(1, (0.4, 0.4, 0.5, 0.5), BASE_TIME + timedelta(seconds=35)),
    )

    # Re-enter entry zone with same track_id
    events = _collect_events(
        engine,
        _make_frame(1, (0.05, 0.05, 0.15, 0.15), BASE_TIME + timedelta(seconds=60)),
    )

    reentry_events = [e for e in events if e.event_type == "REENTRY"]
    assert len(reentry_events) == 1
    assert reentry_events[0].attributes["gap_seconds"] <= 300.0
