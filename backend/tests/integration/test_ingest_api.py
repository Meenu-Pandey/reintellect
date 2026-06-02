"""Integration tests for POST /events/ingest."""

import uuid
from datetime import datetime, timezone


STORE_ID = "test-store"


def _event(**overrides) -> dict:
    base = {
        "event_id": str(uuid.uuid4()),
        "event_type": "ENTRY",
        "store_id": STORE_ID,
        "visitor_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "camera_id": "CAM3",
        "attributes": {},
    }
    base.update(overrides)
    return base


# --- Single event ---

def test_ingest_single_new_event_returns_201(test_client):
    r = test_client.post("/events/ingest", json=_event())
    assert r.status_code == 201
    assert r.json()["duplicate"] is False


def test_ingest_duplicate_event_id_returns_200(test_client):
    e = _event()
    test_client.post("/events/ingest", json=e)
    r = test_client.post("/events/ingest", json=e)
    assert r.status_code == 200
    assert r.json()["duplicate"] is True


def test_ingest_invalid_event_type_returns_422(test_client):
    r = test_client.post("/events/ingest", json=_event(event_type="NOT_VALID"))
    assert r.status_code == 422


def test_ingest_missing_required_field_returns_422(test_client):
    e = _event()
    del e["visitor_id"]
    r = test_client.post("/events/ingest", json=e)
    assert r.status_code == 422


def test_ingest_invalid_timestamp_returns_422(test_client):
    r = test_client.post("/events/ingest", json=_event(timestamp="not-a-date"))
    assert r.status_code == 422


def test_ingest_all_8_event_types(test_client):
    from engine.models import EVENT_TYPES
    for et in EVENT_TYPES:
        r = test_client.post("/events/ingest", json=_event(event_type=et))
        assert r.status_code in (200, 201), f"Failed for type {et}: {r.json()}"


# --- Batch events ---

def test_ingest_batch_all_valid_returns_201(test_client):
    batch = [_event() for _ in range(5)]
    r = test_client.post("/events/ingest", json=batch)
    assert r.status_code == 201
    body = r.json()
    assert body["ingested"] == 5
    assert body["new"] == 5


def test_ingest_batch_one_invalid_rejects_all(test_client):
    good_id = str(uuid.uuid4())
    batch = [
        _event(event_id=good_id),
        _event(event_type="INVALID_TYPE"),
    ]
    r = test_client.post("/events/ingest", json=batch)
    assert r.status_code == 422

    # good event must NOT have been written (atomic rejection)
    r2 = test_client.post("/events/ingest", json=_event(event_id=good_id))
    assert r2.status_code == 201, "Good event was written despite batch rejection"


def test_ingest_batch_exceeds_500_returns_422(test_client):
    batch = [_event() for _ in range(501)]
    r = test_client.post("/events/ingest", json=batch)
    assert r.status_code == 422


def test_ingest_batch_empty_returns_422(test_client):
    r = test_client.post("/events/ingest", json=[])
    assert r.status_code == 422
