"""Integration tests for GET /stores/{id}/heatmap."""


STORE_ID = "test-store"
RESOLUTIONS = {"low": 100, "medium": 400, "high": 1600}


def test_heatmap_returns_200(test_client):
    r = test_client.get(f"/stores/{STORE_ID}/heatmap")
    assert r.status_code == 200


def test_heatmap_low_resolution_returns_100_cells(test_client):
    r = test_client.get(f"/stores/{STORE_ID}/heatmap", params={"resolution": "low"})
    assert r.status_code == 200
    assert r.json()["total_cells"] == 100


def test_heatmap_medium_resolution_returns_400_cells(test_client):
    r = test_client.get(f"/stores/{STORE_ID}/heatmap", params={"resolution": "medium"})
    assert r.status_code == 200
    assert r.json()["total_cells"] == 400


def test_heatmap_high_resolution_returns_1600_cells(test_client):
    r = test_client.get(f"/stores/{STORE_ID}/heatmap", params={"resolution": "high"})
    assert r.status_code == 200
    assert r.json()["total_cells"] == 1600


def test_heatmap_empty_window_all_zeros(test_client):
    from datetime import datetime, timedelta, timezone
    start = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    end = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    r = test_client.get(
        f"/stores/{STORE_ID}/heatmap",
        params={"resolution": "low", "start": start, "end": end},
    )
    assert r.status_code == 200
    all_zero = all(c["density"] == 0.0 for c in r.json()["grid"])
    assert all_zero


def test_heatmap_unknown_store_returns_404(test_client):
    r = test_client.get("/stores/does-not-exist/heatmap")
    assert r.status_code == 404


def test_heatmap_invalid_resolution_returns_400(test_client):
    r = test_client.get(f"/stores/{STORE_ID}/heatmap", params={"resolution": "ultra"})
    assert r.status_code == 400


def test_heatmap_unknown_zone_returns_404(test_client):
    r = test_client.get(
        f"/stores/{STORE_ID}/heatmap", params={"zone_id": "ZONE_NONEXISTENT"}
    )
    assert r.status_code == 404


def test_heatmap_density_values_in_range(test_client):
    r = test_client.get(f"/stores/{STORE_ID}/heatmap", params={"resolution": "low"})
    for cell in r.json()["grid"]:
        assert 0.0 <= cell["density"] <= 1.0
