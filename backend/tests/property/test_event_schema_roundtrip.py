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
