"""
Unit tests for QueueTracker.

Tests:
- Queue depth increments on join
- queue_position is correct
- Abandon emitted at 121s without POS
- No abandon when POS present within 120s
"""

from datetime import datetime, timedelta, timezone

from engine.queue_tracker import QueueTracker


STORE_ID = "test-store"
CAMERA_ID = "CAM1"
BASE_TIME = datetime(2025, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


def test_depth_increments_on_join():
    """Queue depth increments with each join."""
    tracker = QueueTracker(STORE_ID, CAMERA_ID)

    assert tracker.get_depth() == 0

    tracker.join("v1", BASE_TIME)
    assert tracker.get_depth() == 1

    tracker.join("v2", BASE_TIME + timedelta(seconds=5))
    assert tracker.get_depth() == 2


def test_queue_position_is_correct():
    """First joiner gets position 1, second gets position 2."""
    tracker = QueueTracker(STORE_ID, CAMERA_ID)

    e1 = tracker.join("v1", BASE_TIME)
    assert e1.attributes["queue_position"] == 1

    e2 = tracker.join("v2", BASE_TIME + timedelta(seconds=5))
    assert e2.attributes["queue_position"] == 2

    e3 = tracker.join("v3", BASE_TIME + timedelta(seconds=10))
    assert e3.attributes["queue_position"] == 3


def test_abandon_emitted_at_121s_without_pos():
    """BILLING_QUEUE_ABANDON emitted when no POS transaction within 120s."""
    tracker = QueueTracker(STORE_ID, CAMERA_ID)

    tracker.join("v1", BASE_TIME)

    exit_time = BASE_TIME + timedelta(seconds=121)
    event = tracker.check_abandon("v1", exit_time, pos_transactions=[])

    assert event is not None
    assert event.event_type == "BILLING_QUEUE_ABANDON"
    assert event.attributes["wait_seconds"] == 121.0
    assert tracker.get_depth() == 0


def test_no_abandon_when_pos_within_120s():
    """No abandon event when POS transaction exists within 120s window."""
    tracker = QueueTracker(STORE_ID, CAMERA_ID)

    tracker.join("v1", BASE_TIME)

    txn_time = BASE_TIME + timedelta(seconds=60)
    exit_time = BASE_TIME + timedelta(seconds=90)

    event = tracker.check_abandon(
        "v1",
        exit_time,
        pos_transactions=[{"visitor_id": "v1", "timestamp": txn_time}],
    )

    assert event is None
    assert tracker.get_depth() == 0
