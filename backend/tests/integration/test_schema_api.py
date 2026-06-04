"""Integration tests for GET /schema/events."""

from engine.models import EVENT_TYPES


def test_schema_returns_200(test_client):
    r = test_client.get("/schema/events")
    assert r.status_code == 200


def test_schema_content_type(test_client):
    r = test_client.get("/schema/events")
    assert "application/schema+json" in r.headers["content-type"]


def test_schema_contains_all_event_types(test_client):
    r = test_client.get("/schema/events")
    body = r.json()
    returned_types = set(body["properties"]["event_type"]["enum"])
    assert returned_types == EVENT_TYPES


def test_schema_has_required_fields(test_client):
    r = test_client.get("/schema/events")
    body = r.json()
    required = set(body.get("required", []))
    assert "event_id" in required
    assert "event_type" in required
    assert "visitor_id" in required
    assert "timestamp" in required
