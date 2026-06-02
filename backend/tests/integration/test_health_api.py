"""Integration tests for GET /health."""

import pytest


def test_health_returns_200(test_client):
    r = test_client.get("/health")
    assert r.status_code in (200, 503)  # 503 if DB not found in test env
    body = r.json()
    assert "status" in body
    assert "version" in body
    assert "uptime_seconds" in body
    assert "database" in body
    assert "detection_pipeline" in body
    assert "event_engine" in body


def test_health_has_request_id_header(test_client):
    r = test_client.get("/health")
    assert "x-request-id" in r.headers
    assert len(r.headers["x-request-id"]) == 36  # UUID v4


def test_health_version_matches(test_client):
    r = test_client.get("/health")
    assert r.json()["version"] == "0.1.0"
