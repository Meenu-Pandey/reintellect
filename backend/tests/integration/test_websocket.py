"""
Integration tests for WebSocket endpoint.

Tests:
1. Valid store connection receives initial_state payload
2. Unknown store rejected with code 4004
3. Broadcast: connection count increases on connect
4. Disconnect cleans up connection pool
"""

import os
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest
from tests.conftest import _apply_schema


@pytest.fixture(scope="module")
def ws_app():
    """Create a test app with temp DB for WebSocket testing."""
    # Create temp DB
    db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_path = db_file.name
    db_file.close()

    # Apply schema FIRST
    _apply_schema(db_path)

    os.environ["DB_PATH"] = db_path
    os.environ["VIDEO_SOURCE"] = "none"

    import importlib
    import main as main_module
    importlib.reload(main_module)
    app = main_module.create_app()
    yield app

    os.environ.pop("DB_PATH", None)
    os.environ.pop("VIDEO_SOURCE", None)

    try:
        os.unlink(db_path)
    except OSError:
        pass


def test_ws_valid_store_and_unknown_store(ws_app):
    """Test valid connection with initial_state, and unknown store rejection."""
    from starlette.testclient import TestClient

    with TestClient(ws_app) as client:
        # Test 1: Valid store receives initial_state
        with client.websocket_connect("/ws/stores/test-store/events") as ws:
            data = ws.receive_json()
            assert data["type"] == "initial_state"
            assert isinstance(data["events"], list)

        # Test 2: Unknown store gets error with code 4004
        with client.websocket_connect("/ws/stores/nonexistent/events") as ws:
            data = ws.receive_json()
            assert data["type"] == "error"
            assert data["code"] == 4004


def test_ws_connection_count_and_disconnect(ws_app):
    """Test connection pool management."""
    from starlette.testclient import TestClient

    with TestClient(ws_app) as client:
        ws_manager = ws_app.state.ws_manager

        # Before connect
        assert ws_manager.get_connection_count("test-store") == 0

        with client.websocket_connect("/ws/stores/test-store/events") as ws:
            _ = ws.receive_json()  # consume initial_state
            # During connection
            assert ws_manager.get_connection_count("test-store") >= 1

        # After disconnect
        assert ws_manager.get_connection_count("test-store") == 0
