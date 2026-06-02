# Property 5: Zone Dwell Threshold — Validates: Requirements 2.5
#
# ZONE_DWELL is emitted if and only if continuous dwell >= 30s,
# and dwell_seconds in the event is always >= 30.

from datetime import datetime, timedelta, timezone

from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

from engine.zone_tracker import ZoneTracker


# A zone polygon that always contains the test centroid (0.5, 0.5)
CONTAINING_ZONE = {
    "zone_id": "ZONE_TEST",
    "polygon": [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)],
}

# Centroid always inside the zone
CENTROID_INSIDE = (0.5, 0.5)

# Base timestamp
BASE_TIME = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(
    dwell_seconds=st.floats(min_value=0.0, max_value=600.0),
)
def test_zone_dwell_threshold(dwell_seconds: float) -> None:
    """Property 5: ZONE_DWELL emitted iff dwell >= 30s; dwell_seconds >= 30."""
    tracker = ZoneTracker(store_id="store-1", camera_id="CAM2")
    zones = [CONTAINING_ZONE]

    # Simulate entry
    t0 = BASE_TIME
    events_enter = tracker.update(
        visitor_id="visitor-1",
        bbox_centroid=CENTROID_INSIDE,
        timestamp=t0,
        zones=zones,
    )

    # Simulate continued presence after dwell_seconds
    t1 = t0 + timedelta(seconds=dwell_seconds)
    events_dwell = tracker.update(
        visitor_id="visitor-1",
        bbox_centroid=CENTROID_INSIDE,
        timestamp=t1,
        zones=zones,
    )

    # Collect ZONE_DWELL events
    dwell_events = [e for e in events_dwell if e.event_type == "ZONE_DWELL"]

    if dwell_seconds >= 30.0:
        # ZONE_DWELL must be emitted
        assert len(dwell_events) == 1, (
            f"Expected 1 ZONE_DWELL for {dwell_seconds}s dwell, "
            f"got {len(dwell_events)}"
        )
        assert dwell_events[0].attributes["dwell_seconds"] >= 30.0, (
            f"dwell_seconds must be >= 30, "
            f"got {dwell_events[0].attributes['dwell_seconds']}"
        )
    else:
        # No ZONE_DWELL should be emitted
        assert len(dwell_events) == 0, (
            f"Expected no ZONE_DWELL for {dwell_seconds}s dwell, "
            f"got {len(dwell_events)}"
        )


# ---------------------------------------------------------------------------
# Property 7: Queue Position Monotonicity — Validates: Requirements 2.6
#
# Each queue_position = prior_depth + 1 and queue_position >= 1.
# ---------------------------------------------------------------------------

from engine.queue_tracker import QueueTracker


@st.composite
def queue_join_sequence_strategy(draw: st.DrawFn) -> list[str]:
    """Generate a sequence of unique visitor_ids joining a queue."""
    n = draw(st.integers(min_value=1, max_value=50))
    visitor_ids = [f"visitor-{i}" for i in range(n)]
    return visitor_ids


@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(visitor_ids=queue_join_sequence_strategy())
def test_queue_position_monotonicity(visitor_ids: list[str]) -> None:
    """Property 7: Each queue_position = prior_depth + 1 and >= 1."""
    tracker = QueueTracker(store_id="store-1", camera_id="CAM1")
    t = BASE_TIME

    prior_depth = 0
    for i, vid in enumerate(visitor_ids):
        event = tracker.join(vid, t + timedelta(seconds=i))
        pos = event.attributes["queue_position"]

        # queue_position must equal prior_depth + 1
        assert pos == prior_depth + 1, (
            f"Expected queue_position={prior_depth + 1}, got {pos} "
            f"(joiner #{i}, visitor={vid})"
        )

        # queue_position must be >= 1
        assert pos >= 1, (
            f"queue_position must be >= 1, got {pos}"
        )

        prior_depth = tracker.get_depth()
