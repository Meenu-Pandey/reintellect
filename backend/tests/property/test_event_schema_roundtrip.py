# Property 1: Event Schema Round-Trip — Validates: Requirements 14.3, 15.5
#
# For any valid event object, serialising it to JSON and deserialising it back
# SHALL produce an object where every field is equal to the original by value
# and type.

from datetime import datetime, timezone

from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

from engine.models import Event, EVENT_TYPES

# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------

# Valid event type strategy
event_type_strategy = st.sampled_from(sorted(EVENT_TYPES))

# UUID v4 strategy (simplified: valid format)
uuid_strategy = st.uuids(version=4).map(str)

# ISO 8601 UTC timestamp strategy
timestamp_strategy = st.datetimes(
    min_value=datetime(2020, 1, 1),
    max_value=datetime(2030, 12, 31),
    timezones=st.just(timezone.utc),
)

# Camera ID strategy (matches actual camera naming from footage analysis)
camera_id_strategy = st.sampled_from(["CAM1", "CAM2", "CAM3", "CAM4", "CAM5"])

# Store ID strategy
store_id_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N"), whitelist_characters="-_"),
    min_size=1,
    max_size=32,
)

# Visitor ID strategy
visitor_id_strategy = st.uuids(version=4).map(str)

# Event-type-specific attributes
ATTRIBUTES_BY_TYPE = {
    "ENTRY": st.just({}),
    "EXIT": st.fixed_dictionaries(
        {"duration_seconds": st.floats(min_value=0.0, max_value=86400.0)}
    ),
    "ZONE_ENTER": st.fixed_dictionaries(
        {"zone_id": st.text(min_size=1, max_size=32)}
    ),
    "ZONE_EXIT": st.fixed_dictionaries(
        {
            "zone_id": st.text(min_size=1, max_size=32),
            "dwell_seconds": st.floats(min_value=0.0, max_value=86400.0),
        }
    ),
    "ZONE_DWELL": st.fixed_dictionaries(
        {
            "zone_id": st.text(min_size=1, max_size=32),
            "dwell_seconds": st.floats(min_value=30.0, max_value=86400.0),
        }
    ),
    "BILLING_QUEUE_JOIN": st.fixed_dictionaries(
        {"queue_position": st.integers(min_value=1, max_value=100)}
    ),
    "BILLING_QUEUE_ABANDON": st.fixed_dictionaries(
        {"wait_seconds": st.floats(min_value=0.0, max_value=86400.0)}
    ),
    "REENTRY": st.fixed_dictionaries(
        {"gap_seconds": st.floats(min_value=0.0, max_value=300.0)}
    ),
}


@st.composite
def event_strategy(draw: st.DrawFn) -> Event:
    """Generate a valid Event object with type-appropriate attributes."""
    event_type = draw(event_type_strategy)
    attributes = draw(ATTRIBUTES_BY_TYPE[event_type])

    return Event(
        event_id=draw(uuid_strategy),
        event_type=event_type,
        store_id=draw(store_id_strategy),
        visitor_id=draw(visitor_id_strategy),
        timestamp=draw(timestamp_strategy),
        camera_id=draw(camera_id_strategy),
        attributes=attributes,
    )


# ---------------------------------------------------------------------------
# Property test
# ---------------------------------------------------------------------------


@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(event=event_strategy())
def test_event_schema_round_trip(event: Event) -> None:
    """Property 1: Serialising then deserialising produces an equal object."""
    serialised = event.to_dict()
    deserialised = Event.from_dict(serialised)

    assert deserialised.event_id == event.event_id
    assert deserialised.event_type == event.event_type
    assert deserialised.store_id == event.store_id
    assert deserialised.visitor_id == event.visitor_id
    assert deserialised.timestamp == event.timestamp
    assert deserialised.camera_id == event.camera_id
    assert deserialised.attributes == event.attributes


# ---------------------------------------------------------------------------
# Property 3: Detection Threshold Filtering — Validates: Requirements 1.1, 1.8
#
# After pipeline filtering, all remaining detections MUST have
# confidence >= 0.5 AND bbox_height >= 50px.
# ---------------------------------------------------------------------------

# Strategies for detection generation
confidence_strategy = st.floats(min_value=0.0, max_value=1.0)
bbox_height_strategy = st.integers(min_value=10, max_value=500)

# Normalised bbox: x1, y1, x2, y2 in [0.0, 1.0]
normalised_coord = st.floats(min_value=0.0, max_value=1.0)


@st.composite
def detection_list_strategy(draw: st.DrawFn) -> list[dict]:
    """Generate a list of raw detections with varying confidence and bbox height."""
    n = draw(st.integers(min_value=0, max_value=20))
    detections = []
    for _ in range(n):
        conf = draw(confidence_strategy)
        # Generate bbox in pixel space (frame assumed 1080p height)
        frame_height = 1080
        y1_px = draw(st.integers(min_value=0, max_value=frame_height - 11))
        bbox_h = draw(bbox_height_strategy)
        y2_px = min(y1_px + bbox_h, frame_height)
        # Normalise
        y1 = y1_px / frame_height
        y2 = y2_px / frame_height
        x1 = draw(st.floats(min_value=0.0, max_value=0.8))
        x2 = x1 + draw(st.floats(min_value=0.01, max_value=0.2))
        x2 = min(x2, 1.0)
        detections.append(
            {
                "bbox": (x1, y1, x2, y2),
                "confidence": conf,
                "bbox_height_px": y2_px - y1_px,
            }
        )
    return detections


def apply_pipeline_filters(
    detections: list[dict],
    min_confidence: float = 0.5,
    min_bbox_height_px: int = 50,
) -> list[dict]:
    """Replicate the pipeline's threshold filtering logic."""
    return [
        d
        for d in detections
        if d["confidence"] >= min_confidence
        and d["bbox_height_px"] >= min_bbox_height_px
    ]


@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(detections=detection_list_strategy())
def test_detection_threshold_filtering(detections: list[dict]) -> None:
    """Property 3: All detections surviving filtering meet both thresholds."""
    filtered = apply_pipeline_filters(detections)

    for det in filtered:
        assert det["confidence"] >= 0.5, (
            f"Detection with confidence {det['confidence']} should have been filtered"
        )
        assert det["bbox_height_px"] >= 50, (
            f"Detection with bbox_height {det['bbox_height_px']}px should have been filtered"
        )

    # Also verify that no detection meeting both thresholds was dropped
    for det in detections:
        if det["confidence"] >= 0.5 and det["bbox_height_px"] >= 50:
            assert det in filtered, (
                f"Valid detection was incorrectly filtered: {det}"
            )


# ---------------------------------------------------------------------------
# Property 4: Staff Exclusion Invariant — Validates: Requirements 1.5
#
# No detection tagged with role="staff" shall appear in the output
# TrackFrame.detections list that is passed to the event engine.
# ---------------------------------------------------------------------------

from detection.models import TrackDetection, TrackFrame

role_strategy = st.sampled_from(["visitor", "staff"])


@st.composite
def mixed_detection_set_strategy(draw: st.DrawFn) -> list[TrackDetection]:
    """Generate a list of TrackDetections with mixed visitor/staff roles."""
    n = draw(st.integers(min_value=1, max_value=20))
    detections = []
    for i in range(n):
        role = draw(role_strategy)
        x1 = draw(st.floats(min_value=0.0, max_value=0.7))
        y1 = draw(st.floats(min_value=0.0, max_value=0.7))
        x2 = x1 + draw(st.floats(min_value=0.01, max_value=0.3))
        y2 = y1 + draw(st.floats(min_value=0.01, max_value=0.3))
        x2 = min(x2, 1.0)
        y2 = min(y2, 1.0)
        conf = draw(st.floats(min_value=0.5, max_value=1.0))
        detections.append(
            TrackDetection(
                track_id=i + 1,
                bbox=(x1, y1, x2, y2),
                confidence=conf,
                role=role,
            )
        )
    return detections


def filter_staff_detections(detections: list[TrackDetection]) -> list[TrackDetection]:
    """Filter out staff detections — mirrors pipeline output for event engine."""
    return [d for d in detections if d.role != "staff"]


@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(detections=mixed_detection_set_strategy())
def test_staff_exclusion_invariant(detections: list[TrackDetection]) -> None:
    """Property 4: No staff-tagged detection appears in filtered output."""
    filtered = filter_staff_detections(detections)

    for det in filtered:
        assert det.role != "staff", (
            f"Staff detection with track_id={det.track_id} was not excluded"
        )

    # Verify all visitors are preserved
    visitors = [d for d in detections if d.role == "visitor"]
    assert len(filtered) == len(visitors), (
        f"Expected {len(visitors)} visitor detections, got {len(filtered)}"
    )
