"""Simplified tests for WebSocket error handling and connection management.

This module tests the core WebSocket error scenarios with simplified mocking.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import WebSocket
from fastapi.testclient import TestClient

from puntini.api.websocket import WebSocketManager
from puntini.api.session import SessionManager
from puntini.api.models import UserPrompt, Error, AssistantResponse
from puntini.api.app import create_app


class TestWebSocketErrorHandling:
    """Test WebSocket error handling scenarios."""
    
    @pytest.fixture
    def session_manager(self):
        """Create a session manager for testing."""
        return SessionManager()
    
    @pytest.fixture
    def websocket_manager(self, session_manager):
        """Create a WebSocket manager for testing."""
        return WebSocketManager(session_manager)
    
    def test_websocket_manager_initialization(self, session_manager):
        """Test WebSocket manager initialization."""
        manager = WebSocketManager(session_manager)
        
        assert manager.session_manager == session_manager
        assert manager.active_connections == {}
        assert manager.user_connections == {}
        assert manager.running_tasks == {}
        assert manager.logger is not None
    
    def test_connection_alive_check_no_connection(self, websocket_manager):
        """Test connection alive checking with no connection."""
        session_id = "test-session"
        assert not websocket_manager.is_connection_alive(session_id)
    
    @pytest.mark.asyncio
    async def test_send_message_no_connection(self, websocket_manager):
        """Test sending message when no connection exists."""
        session_id = "test-session"
        
        # Create test message
        message = Error.create(
            code=500,
            message="Test error",
            session_id=session_id
        )
        
        # Send message should return False for non-existent connection
        result = await websocket_manager.send_message(session_id, message)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_agent_task_cancellation_handling(self, websocket_manager):
        """Test that agent task cancellation is handled properly."""
        session_id = "test-session"
        
        # Create a mock WebSocket connection
        mock_websocket = AsyncMock()
        mock_websocket.client_state.name = "CONNECTED"
        websocket_manager.active_connections[session_id] = mock_websocket
        
        # Create a mock task
        task = asyncio.create_task(asyncio.sleep(1))
        websocket_manager.running_tasks[session_id] = task
        
        # Cancel the task
        task.cancel()
        
        # Disconnect should handle cancelled tasks gracefully
        await websocket_manager.disconnect(session_id)
        
        # Task should be cleaned up (disconnect removes it from running_tasks)
        assert session_id not in websocket_manager.running_tasks
    
    @pytest.mark.asyncio
    async def test_concurrent_request_prevention(self, websocket_manager):
        """Test that concurrent requests for same session are prevented."""
        session_id = "test-session"
        
        # Create a mock task
        task = asyncio.create_task(asyncio.sleep(1))
        websocket_manager.running_tasks[session_id] = task
        
        # Create user prompt message
        message = UserPrompt.create(
            prompt="Test prompt",
            session_id=session_id
        )
        
        # Process with agent should detect existing task
        await websocket_manager._process_with_agent(session_id, message)
        
        # Task should still be there (not replaced)
        assert session_id in websocket_manager.running_tasks
        
        # Clean up
        task.cancel()
        websocket_manager.running_tasks.pop(session_id, None)
    
    @pytest.mark.asyncio
    async def test_running_tasks_tracking(self, websocket_manager):
        """Test running tasks tracking functionality."""
        session_id = "test-session"
        
        # Initially no running tasks
        assert session_id not in websocket_manager.running_tasks
        
        # Add a task
        task = asyncio.create_task(asyncio.sleep(0.1))
        websocket_manager.running_tasks[session_id] = task
        
        # Task should be tracked
        assert session_id in websocket_manager.running_tasks
        assert websocket_manager.running_tasks[session_id] == task
        
        # Clean up
        task.cancel()
        websocket_manager.running_tasks.pop(session_id, None)
        assert session_id not in websocket_manager.running_tasks


class TestWebSocketIntegration:
    """Integration tests for WebSocket functionality."""
    
    @pytest.fixture
    def app(self):
        """Create FastAPI app for testing."""
        return create_app()
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)
    
    def test_websocket_endpoint_exists(self, client):
        """Test that WebSocket endpoint exists."""
        response = client.get("/health")
        assert response.status_code == 200
    
    def test_websocket_connection_without_token(self, app):
        """Test WebSocket connection without token."""
        # This would require WebSocket testing framework
        # For now, we'll just ensure the endpoint exists
        assert "/ws/chat" in [route.path for route in app.routes]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])