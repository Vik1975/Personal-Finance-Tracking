"""Tests for WebSocket functionality."""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.api.websocket import manager, notify_document_processing, notify_transaction_event


class TestWebSocketConnection:
    """Test WebSocket connection handling."""

    def test_websocket_without_token(self):
        """Test WebSocket connection fails without token."""
        client = TestClient(app)
        with pytest.raises(Exception):
            with client.websocket_connect("/ws"):
                pass

    def test_websocket_with_invalid_token(self):
        """Test WebSocket connection fails with invalid token."""
        client = TestClient(app)
        with pytest.raises(Exception):
            with client.websocket_connect("/ws?token=invalid_token"):
                pass


class TestConnectionManager:
    """Test ConnectionManager class."""

    def test_connection_manager_initialization(self):
        """Test ConnectionManager initializes with empty connections."""
        manager_test = type(manager)()
        assert manager_test.active_connections == {}

    def test_disconnect_nonexistent_user(self):
        """Test disconnecting non-existent user doesn't raise error."""
        manager_test = type(manager)()
        # Should not raise exception
        manager_test.disconnect(None, 999)
        assert 999 not in manager_test.active_connections


class TestNotificationFunctions:
    """Test notification helper functions."""

    @pytest.mark.asyncio
    async def test_notify_document_processing(self):
        """Test notify_document_processing doesn't raise exceptions."""
        # Should not raise exception for non-existent user
        await notify_document_processing(
            user_id=999,
            document_id=1,
            status="started"
        )

    @pytest.mark.asyncio
    async def test_notify_document_processing_with_progress(self):
        """Test notify_document_processing with progress."""
        await notify_document_processing(
            user_id=999,
            document_id=1,
            status="progress",
            progress=50
        )

    @pytest.mark.asyncio
    async def test_notify_document_processing_with_error(self):
        """Test notify_document_processing with error."""
        await notify_document_processing(
            user_id=999,
            document_id=1,
            status="failed",
            error="Test error"
        )

    @pytest.mark.asyncio
    async def test_notify_transaction_event(self):
        """Test notify_transaction_event doesn't raise exceptions."""
        await notify_transaction_event(
            user_id=999,
            event="created",
            transaction_data={"id": 1, "amount": 100}
        )


class TestWebSocketRouteRegistration:
    """Test WebSocket route is properly registered."""

    def test_websocket_route_exists(self):
        """Test WebSocket route is registered in the app."""
        routes = [route.path for route in app.routes if hasattr(route, 'path')]
        assert "/ws" in routes

    def test_websocket_route_accepts_websocket(self):
        """Test WebSocket route accepts WebSocket connections."""
        ws_routes = [
            route for route in app.routes
            if hasattr(route, 'path') and route.path == "/ws"
        ]
        assert len(ws_routes) > 0
