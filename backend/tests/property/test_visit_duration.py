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
