"""
Unit tests for ZoneTracker state machine.

Tests:
- OUTSIDE → IN_ZONE transition
- IN_ZONE → DWELL_EMITTED at 30s
- DWELL_EMITTED → OUTSIDE on exit
- Track-loss ZONE_EXIT
"""

from datetime import datetime, timedelta, timezone

from engine.zone_tracker import ZoneTracker


STORE_ID = "test-store"
CAMERA_ID = "CAM2"
BASE_TIME = datetime(2025, 6, 1, 12, 0, 0, tzinfo=timezone.utc)

ZONE = {
    "zone_id": "ZONE_MAKEUP",
    "polygon": [(0.3, 0.3), (0.7, 0.3), (0.7, 0.7), (0.3, 0.7)],
}
ZONES = [ZONE]

CENTROID_INSIDE = (0.5, 0.5)
CENTROID_OUTSIDE = (0.1, 0.1)


def test_outside_to_in_zone():
    """OUTSIDE → IN_ZONE emits ZONE_ENTER."""
    tracker = ZoneTracker(STORE_ID, CAMERA_ID)

    events = tracker.update("v1", CENTROID_INSIDE, BASE_TIME, ZONES)

    assert len(events) == 1
    assert events[0].event_type == "ZONE_ENTER"
    assert events[0].attributes["zone_id"] == "ZONE_MAKEUP"
    assert events[0].visitor_id == "v1"


def test_in_zone_to_dwell_emitted():
    """IN_ZONE → DWELL_EMITTED at 30s emits ZONE_DWELL."""
    tracker = ZoneTracker(STORE_ID, CAMERA_ID)

    # Enter zone
    tracker.update("v1", CENTROID_INSIDE, BASE_TIME, ZONES)

    # Stay for exactly 30s
    events = tracker.update(
        "v1", CENTROID_INSIDE, BASE_TIME + timedelta(seconds=30), ZONES
    )

    assert len(events) == 1
    assert events[0].event_type == "ZONE_DWELL"
    assert events[0].attributes["dwell_seconds"] >= 30.0
    assert events[0].attributes["zone_id"] == "ZONE_MAKEUP"


def test_dwell_emitted_to_outside():
    """DWELL_EMITTED → OUTSIDE on exit emits ZONE_EXIT."""
    tracker = ZoneTracker(STORE_ID, CAMERA_ID)

    # Enter zone
    tracker.update("v1", CENTROID_INSIDE, BASE_TIME, ZONES)

    # Trigger dwell at 30s
    tracker.update(
        "v1", CENTROID_INSIDE, BASE_TIME + timedelta(seconds=30), ZONES
    )

    # Leave zone at 45s
    events = tracker.update(
        "v1", CENTROID_OUTSIDE, BASE_TIME + timedelta(seconds=45), ZONES
    )

    assert len(events) == 1
    assert events[0].event_type == "ZONE_EXIT"
    assert events[0].attributes["zone_id"] == "ZONE_MAKEUP"
    assert events[0].attributes["dwell_seconds"] >= 45.0


def test_track_loss_emits_zone_exit():
    """Track loss emits ZONE_EXIT with accumulated dwell."""
    tracker = ZoneTracker(STORE_ID, CAMERA_ID)

    # Enter zone
    tracker.update("v1", CENTROID_INSIDE, BASE_TIME, ZONES)

    # Stay for 20s (no dwell event yet)
    tracker.update(
        "v1", CENTROID_INSIDE, BASE_TIME + timedelta(seconds=20), ZONES
    )

    # Track lost at 25s
    events = tracker.update(
        "v1",
        CENTROID_INSIDE,
        BASE_TIME + timedelta(seconds=25),
        ZONES,
        track_lost=True,
    )

    assert len(events) == 1
    assert events[0].event_type == "ZONE_EXIT"
    assert events[0].attributes["zone_id"] == "ZONE_MAKEUP"
    assert events[0].attributes["dwell_seconds"] >= 25.0
