"""Integration tests for GET /stores/{id}/metrics."""

import uuid
from datetime import datetime, timezone


STORE_ID = "test-store"


def test_metrics_returns_200(test_client):
    r = test_client.get(f"/stores/{STORE_ID}/metrics")
    assert r.status_code == 200


def test_metrics_has_required_fields(test_client):
    r = test_client.get(f"/stores/{STORE_ID}/metrics")
    body = r.json()
    required = ["store_id", "unique_visitors", "conversion_rate",
                "avg_dwell_per_zone", "queue_depth", "abandonment_rate",
                "avg_visit_duration_seconds"]
    for field in required:
        assert field in body, f"Missing field: {field}"


def test_metrics_zero_visitors_gives_zero_conversion(test_client):
    r = test_client.get(f"/stores/{STORE_ID}/metrics")
    body = r.json()
    if body["unique_visitors"] == 0:
        assert body["conversion_rate"] == 0.0
        assert body["abandonment_rate"] == 0.0


def test_metrics_unknown_store_returns_404(test_client):
    r = test_client.get("/stores/does-not-exist/metrics")
    assert r.status_code == 404


def test_metrics_invalid_date_returns_400(test_client):
    r = test_client.get(
        f"/stores/{STORE_ID}/metrics",
        params={"start": "not-a-date"},
    )
    assert r.status_code == 400


def test_metrics_reflects_ingested_entry_events(test_client):
    """After ingesting ENTRY events, unique_visitors should increase."""
    before = test_client.get(f"/stores/{STORE_ID}/metrics").json()["unique_visitors"]
    now = datetime.now(timezone.utc).isoformat()

    for _ in range(3):
        test_client.post("/events/ingest", json={
            "event_id": str(uuid.uuid4()),
            "event_type": "ENTRY",
            "store_id": STORE_ID,
            "visitor_id": str(uuid.uuid4()),
            "timestamp": now,
            "camera_id": "CAM3",
            "attributes": {},
        })

    after = test_client.get(f"/stores/{STORE_ID}/metrics").json()["unique_visitors"]
    assert after >= before + 3
