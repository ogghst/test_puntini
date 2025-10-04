"""Test to verify WebSocket connection fix."""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from puntini.api.websocket import WebSocketManager
from puntini.api.session import SessionManager


class TestWebSocketFix:
    """Test cases for WebSocket connection fix."""
    
    @pytest.mark.asyncio
    async def test_websocket_connection_flow(self):
        """Test that WebSocket connection doesn't have duplicate accept calls."""
        # Mock dependencies
        mock_websocket = AsyncMock()
        mock_websocket.accept = AsyncMock()
        mock_websocket.close = AsyncMock()
        
        # Mock authentication
        with patch('puntini.api.websocket.get_current_user_websocket') as mock_auth:
            mock_auth.return_value = "testuser"
            
            # Create WebSocket manager
            session_manager = SessionManager()
            ws_manager = WebSocketManager(session_manager)
            
            # Test connection
            session_id = await ws_manager.connect(mock_websocket, "valid_token")
            
            # Verify that accept was called exactly once
            mock_websocket.accept.assert_called_once()
            
            # Verify that close was not called (since auth succeeded)
            mock_websocket.close.assert_not_called()
            
            # Verify session was created
            assert session_id is not None
            assert session_id in ws_manager.active_connections
    
    @pytest.mark.asyncio
    async def test_websocket_connection_auth_failure(self):
        """Test WebSocket connection with invalid token."""
        # Mock dependencies
        mock_websocket = AsyncMock()
        mock_websocket.accept = AsyncMock()
        mock_websocket.close = AsyncMock()
        
        # Mock authentication failure
        with patch('puntini.api.websocket.get_current_user_websocket') as mock_auth:
            mock_auth.return_value = None
            
            # Create WebSocket manager
            session_manager = SessionManager()
            ws_manager = WebSocketManager(session_manager)
            
            # Test connection with invalid token
            session_id = await ws_manager.connect(mock_websocket, "invalid_token")
            
            # Verify that accept was NOT called (since auth failed)
            mock_websocket.accept.assert_not_called()
            
            # Verify that close was called
            mock_websocket.close.assert_called_once_with(code=1008, reason="Invalid token")
            
            # Verify no session was created
            assert session_id is None
    
    def test_websocket_endpoint_signature(self):
        """Test that WebSocket endpoint has correct signature."""
        from puntini.api.app import create_app
        
        app = create_app()
        
        # Find WebSocket route
        ws_route = None
        for route in app.routes:
            if hasattr(route, 'path') and route.path == '/ws/chat':
                ws_route = route
                break
        
        assert ws_route is not None, "WebSocket endpoint not found"
        assert hasattr(ws_route, 'endpoint'), "WebSocket route has no endpoint"
        
        # Check that the endpoint function has correct signature
        endpoint_func = ws_route.endpoint
        import inspect
        sig = inspect.signature(endpoint_func)
        
        # Should have websocket and token parameters
        params = list(sig.parameters.keys())
        assert 'websocket' in params, f"Missing 'websocket' parameter: {params}"
        assert 'token' in params, f"Missing 'token' parameter: {params}"
    
    @pytest.mark.asyncio
    async def test_send_message_to_closed_connection(self):
        """Test that sending messages to closed connections is handled gracefully."""
        # Mock dependencies
        mock_websocket = AsyncMock()
        mock_websocket.client_state = MagicMock()
        mock_websocket.client_state.name = "DISCONNECTED"  # Simulate closed connection
        mock_websocket.send_text = AsyncMock()
        
        # Mock authentication
        with patch('puntini.api.websocket.get_current_user_websocket') as mock_auth:
            mock_auth.return_value = "testuser"
            
            # Create WebSocket manager
            session_manager = SessionManager()
            ws_manager = WebSocketManager(session_manager)
            
            # Connect first
            session_id = await ws_manager.connect(mock_websocket, "valid_token")
            assert session_id is not None
            
            # Simulate connection being closed by client
            mock_websocket.client_state.name = "DISCONNECTED"
            
            # Try to send a message
            from puntini.api.models import Ping
            message = Ping(session_id=session_id)
            
            # Should return False and clean up the connection
            result = await ws_manager.send_message(session_id, message)
            assert result is False
            
            # Connection should be cleaned up
            assert session_id not in ws_manager.active_connections
    
    @pytest.mark.asyncio
    async def test_send_message_runtime_error_handling(self):
        """Test that RuntimeError from closed WebSocket is handled gracefully."""
        # Mock dependencies
        mock_websocket = AsyncMock()
        mock_websocket.client_state = MagicMock()
        mock_websocket.client_state.name = "CONNECTED"
        mock_websocket.send_text = AsyncMock()
        
        # Make send_text raise the specific RuntimeError
        mock_websocket.send_text.side_effect = RuntimeError('Cannot call "send" once a close message has been sent.')
        
        # Mock authentication
        with patch('puntini.api.websocket.get_current_user_websocket') as mock_auth:
            mock_auth.return_value = "testuser"
            
            # Create WebSocket manager
            session_manager = SessionManager()
            ws_manager = WebSocketManager(session_manager)
            
            # Connect first
            session_id = await ws_manager.connect(mock_websocket, "valid_token")
            assert session_id is not None
            
            # Try to send a message
            from puntini.api.models import Ping
            message = Ping(session_id=session_id)
            
            # Should return False and clean up the connection
            result = await ws_manager.send_message(session_id, message)
            assert result is False
            
            # Connection should be cleaned up
            assert session_id not in ws_manager.active_connections
    
    def test_is_connection_alive(self):
        """Test the is_connection_alive helper method."""
        # Create WebSocket manager
        session_manager = SessionManager()
        ws_manager = WebSocketManager(session_manager)
        
        # Test with non-existent session
        assert ws_manager.is_connection_alive("nonexistent") is False
        
        # Mock a connected WebSocket
        mock_websocket = AsyncMock()
        mock_websocket.client_state = MagicMock()
        mock_websocket.client_state.name = "CONNECTED"
        
        # Add to active connections
        ws_manager.active_connections["test_session"] = mock_websocket
        
        # Should return True for connected session
        assert ws_manager.is_connection_alive("test_session") is True
        
        # Simulate disconnected state
        mock_websocket.client_state.name = "DISCONNECTED"
        assert ws_manager.is_connection_alive("test_session") is False


if __name__ == "__main__":
    # Run a simple test
    import asyncio
    
    async def run_tests():
        test = TestWebSocketFix()
        await test.test_websocket_connection_flow()
        await test.test_websocket_connection_auth_failure()
        test.test_websocket_endpoint_signature()
        await test.test_send_message_to_closed_connection()
        await test.test_send_message_runtime_error_handling()
        test.test_is_connection_alive()
        print("All WebSocket fix tests passed!")
    
    asyncio.run(run_tests())
