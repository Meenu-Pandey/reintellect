"""Integration tests for GET /stores/{id}/anomalies."""


STORE_ID = "test-store"


def test_anomalies_returns_200(test_client):
    r = test_client.get(f"/stores/{STORE_ID}/anomalies")
    assert r.status_code == 200


def test_anomalies_empty_returns_empty_list(test_client):
    r = test_client.get(f"/stores/{STORE_ID}/anomalies")
    body = r.json()
    assert "anomalies" in body
    assert isinstance(body["anomalies"], list)
    assert "count" in body


def test_anomalies_unknown_store_returns_404(test_client):
    r = test_client.get("/stores/nonexistent/anomalies")
    assert r.status_code == 404


def test_anomalies_start_gt_end_returns_400(test_client):
    from datetime import datetime, timedelta, timezone
    now = datetime.now(timezone.utc)
    r = test_client.get(
        f"/stores/{STORE_ID}/anomalies",
        params={
            "start": (now + timedelta(hours=1)).isoformat(),
            "end": now.isoformat(),
        },
    )
    assert r.status_code == 400


def test_anomalies_malformed_start_returns_400(test_client):
    r = test_client.get(
        f"/stores/{STORE_ID}/anomalies",
        params={"start": "not-a-date"},
    )
    assert r.status_code == 400


def test_anomalies_malformed_end_returns_400(test_client):
    r = test_client.get(
        f"/stores/{STORE_ID}/anomalies",
        params={"end": "not-a-date"},
    )
    assert r.status_code == 400


def test_anomalies_ordered_by_detected_at_desc(test_client):
    r = test_client.get(f"/stores/{STORE_ID}/anomalies")
    anomalies = r.json()["anomalies"]
    if len(anomalies) >= 2:
        timestamps = [a["detected_at"] for a in anomalies]
        assert timestamps == sorted(timestamps, reverse=True)


def test_anomalies_count_matches_list_length(test_client):
    r = test_client.get(f"/stores/{STORE_ID}/anomalies")
    body = r.json()
    assert body["count"] == len(body["anomalies"])
