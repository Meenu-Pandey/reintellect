"""Integration tests for GET /stores/{id}/funnel."""


STORE_ID = "test-store"


def test_funnel_returns_200(test_client):
    r = test_client.get(f"/stores/{STORE_ID}/funnel")
    assert r.status_code == 200


def test_funnel_has_required_fields(test_client):
    r = test_client.get(f"/stores/{STORE_ID}/funnel")
    body = r.json()
    assert "stages" in body
    assert "data_available" in body


def test_funnel_empty_data_has_data_available_false(test_client):
    from datetime import datetime, timedelta, timezone
    # Window with no data
    start = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    end = (datetime.now(timezone.utc) - timedelta(days=29)).isoformat()
    r = test_client.get(
        f"/stores/{STORE_ID}/funnel",
        params={"start": start, "end": end},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["data_available"] is False
    assert body["stages"] == []


def test_funnel_unknown_store_returns_404(test_client):
    r = test_client.get("/stores/does-not-exist/funnel")
    assert r.status_code == 404


def test_funnel_window_exceeds_90_days_returns_400(test_client):
    from datetime import datetime, timedelta, timezone
    start = (datetime.now(timezone.utc) - timedelta(days=91)).isoformat()
    end = datetime.now(timezone.utc).isoformat()
    r = test_client.get(
        f"/stores/{STORE_ID}/funnel",
        params={"start": start, "end": end},
    )
    assert r.status_code == 400


def test_funnel_entry_rate_in_valid_range(test_client):
    r = test_client.get(f"/stores/{STORE_ID}/funnel")
    body = r.json()
    for stage in body.get("stages", []):
        assert 0.0 <= stage["entry_rate"] <= 1.0


def test_funnel_with_data_has_data_available_true(test_client):
    """After inserting ENTRY + ZONE_ENTER events, funnel should return data."""
    import uuid
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).isoformat()
    vid = str(uuid.uuid4())
    # Insert ENTRY so total_visitors > 0
    test_client.post("/events/ingest", json={
        "event_id": str(uuid.uuid4()),
        "event_type": "ENTRY",
        "store_id": STORE_ID,
        "visitor_id": vid,
        "timestamp": now,
        "camera_id": "CAM3",
        "attributes": {},
    })
    # Insert ZONE_ENTER
    test_client.post("/events/ingest", json={
        "event_id": str(uuid.uuid4()),
        "event_type": "ZONE_ENTER",
        "store_id": STORE_ID,
        "visitor_id": vid,
        "timestamp": now,
        "camera_id": "CAM2",
        "attributes": {"zone_id": "ZONE_MAKEUP"},
    })
    r = test_client.get(f"/stores/{STORE_ID}/funnel")
    assert r.status_code == 200
    body = r.json()
    assert body["data_available"] is True
    assert body["total_visitors"] >= 1


def test_funnel_invalid_start_returns_400(test_client):
    r = test_client.get(f"/stores/{STORE_ID}/funnel", params={"start": "bad"})
    assert r.status_code == 400


def test_funnel_invalid_end_returns_400(test_client):
    r = test_client.get(f"/stores/{STORE_ID}/funnel", params={"end": "bad"})
    assert r.status_code == 400
