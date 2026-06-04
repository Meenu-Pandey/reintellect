"""Integration tests for POST /stores and POST /stores/{id}/transactions."""

import uuid
from datetime import datetime, timedelta, timezone


VALID_LAYOUT = {
    "store_id": "api-test-store",
    "name": "API Test Store",
    "timezone": "UTC",
    "zones": [
        {
            "zone_id": "ZONE_A",
            "zone_type": "entry",
            "name": "Entry",
            "polygon": [[0.0, 0.0], [0.2, 0.0], [0.2, 0.2], [0.0, 0.2]],
        },
        {
            "zone_id": "ZONE_B",
            "zone_type": "floor",
            "name": "Floor",
            "polygon": [[0.3, 0.3], [0.7, 0.3], [0.7, 0.7], [0.3, 0.7]],
        },
    ],
    "cameras": [{"camera_id": "CAM1", "name": "Main Camera"}],
}


def test_create_store_valid_layout(test_client):
    r = test_client.post("/stores", json=VALID_LAYOUT)
    assert r.status_code == 200
    body = r.json()
    assert body["store_id"] == "api-test-store"
    assert body["zones_count"] == 2


def test_create_store_polygon_too_few_vertices(test_client):
    bad = {**VALID_LAYOUT, "store_id": "bad-store", "zones": [
        {"zone_id": "Z1", "zone_type": "floor", "polygon": [[0.0, 0.0], [0.5, 0.5]]},
    ]}
    r = test_client.post("/stores", json=bad)
    assert r.status_code == 422


def test_create_store_self_intersecting_polygon(test_client):
    bad = {**VALID_LAYOUT, "store_id": "bad-store2", "zones": [
        {"zone_id": "Z1", "zone_type": "floor",
         "polygon": [[0.0, 0.0], [1.0, 1.0], [1.0, 0.0], [0.0, 1.0]]},
    ]}
    r = test_client.post("/stores", json=bad)
    assert r.status_code == 422


def test_create_store_invalid_zone_type(test_client):
    bad = {**VALID_LAYOUT, "store_id": "bad-store3", "zones": [
        {"zone_id": "Z1", "zone_type": "invalid_type",
         "polygon": [[0.0, 0.0], [0.5, 0.0], [0.5, 0.5], [0.0, 0.5]]},
    ]}
    r = test_client.post("/stores", json=bad)
    assert r.status_code == 422


def test_transaction_valid(test_client):
    # Ensure store exists
    test_client.post("/stores", json=VALID_LAYOUT)

    txn = {
        "transaction_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "amount": 499.0,
    }
    r = test_client.post(f"/stores/{VALID_LAYOUT['store_id']}/transactions", json=txn)
    assert r.status_code == 201


def test_transaction_old_timestamp(test_client):
    test_client.post("/stores", json=VALID_LAYOUT)
    txn = {
        "transaction_id": str(uuid.uuid4()),
        "timestamp": (datetime.now(timezone.utc) - timedelta(hours=25)).isoformat(),
        "amount": 100.0,
    }
    r = test_client.post(f"/stores/{VALID_LAYOUT['store_id']}/transactions", json=txn)
    assert r.status_code == 422


def test_transaction_unknown_store(test_client):
    txn = {
        "transaction_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "amount": 100.0,
    }
    r = test_client.post("/stores/nonexistent-store/transactions", json=txn)
    assert r.status_code == 404
