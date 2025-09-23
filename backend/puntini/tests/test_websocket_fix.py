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


if __name__ == "__main__":
    # Run a simple test
    import asyncio
    
    async def run_tests():
        test = TestWebSocketFix()
        await test.test_websocket_connection_flow()
        await test.test_websocket_connection_auth_failure()
        test.test_websocket_endpoint_signature()
        print("All WebSocket fix tests passed!")
    
    asyncio.run(run_tests())
