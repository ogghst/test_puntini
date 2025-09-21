"""Tests for API message models."""

import pytest
from datetime import datetime

from puntini.api.models import (
    MessageType,
    UserPrompt,
    AssistantResponse,
    Reasoning,
    Debug,
    GraphUpdate,
    Error,
    SessionReady,
    InitSession,
    CloseSession,
    ChatHistory,
    Ping,
    Pong,
    parse_message,
)


class TestMessageTypes:
    """Test message type creation and parsing."""
    
    def test_user_prompt_creation(self):
        """Test UserPrompt message creation."""
        prompt = UserPrompt.create("Hello, world!", "session-123")
        
        assert prompt.type == MessageType.USER_PROMPT
        assert prompt.data["prompt"] == "Hello, world!"
        assert prompt.session_id == "session-123"
        assert prompt.timestamp is not None
    
    def test_assistant_response_creation(self):
        """Test AssistantResponse message creation."""
        response = AssistantResponse.create("Hello back!", chunk=True, session_id="session-123")
        
        assert response.type == MessageType.ASSISTANT_RESPONSE
        assert response.data["text"] == "Hello back!"
        assert response.data["chunk"] is True
        assert response.session_id == "session-123"
    
    def test_reasoning_creation(self):
        """Test Reasoning message creation."""
        steps = ["Step 1", "Step 2", "Step 3"]
        reasoning = Reasoning.create(steps, "session-123")
        
        assert reasoning.type == MessageType.REASONING
        assert reasoning.data["steps"] == steps
        assert reasoning.session_id == "session-123"
    
    def test_debug_creation(self):
        """Test Debug message creation."""
        debug = Debug.create("Test message", "warning", "session-123")
        
        assert debug.type == MessageType.DEBUG
        assert debug.data["message"] == "Test message"
        assert debug.data["level"] == "warning"
        assert debug.session_id == "session-123"
    
    def test_error_creation(self):
        """Test Error message creation."""
        error = Error.create(400, "Bad request", "session-123")
        
        assert error.type == MessageType.ERROR
        assert error.error["code"] == 400
        assert error.error["message"] == "Bad request"
        assert error.session_id == "session-123"
    
    def test_session_ready_creation(self):
        """Test SessionReady message creation."""
        ready = SessionReady(session_id="session-123")
        
        assert ready.type == MessageType.SESSION_READY
        assert "session_id" in ready.data
        assert "initial_graph" in ready.data
        assert "status" in ready.data
        assert ready.session_id == "session-123"
    
    def test_ping_pong_creation(self):
        """Test Ping and Pong message creation."""
        ping = Ping(session_id="session-123")
        pong = Pong(session_id="session-123")
        
        assert ping.type == MessageType.PING
        assert pong.type == MessageType.PONG
        assert ping.session_id == "session-123"
        assert pong.session_id == "session-123"


class TestMessageParsing:
    """Test message parsing functionality."""
    
    def test_parse_user_prompt(self):
        """Test parsing UserPrompt message."""
        data = {
            "type": "user_prompt",
            "data": {"prompt": "Hello, world!"},
            "session_id": "session-123"
        }
        
        message = parse_message(data)
        assert isinstance(message, UserPrompt)
        assert message.data["prompt"] == "Hello, world!"
        assert message.session_id == "session-123"
    
    def test_parse_assistant_response(self):
        """Test parsing AssistantResponse message."""
        data = {
            "type": "assistant_response",
            "data": {"text": "Hello back!", "chunk": True},
            "session_id": "session-123"
        }
        
        message = parse_message(data)
        assert isinstance(message, AssistantResponse)
        assert message.data["text"] == "Hello back!"
        assert message.data["chunk"] is True
    
    def test_parse_error(self):
        """Test parsing Error message."""
        data = {
            "type": "error",
            "data": {},
            "error": {"code": 400, "message": "Bad request"},
            "session_id": "session-123"
        }
        
        message = parse_message(data)
        assert isinstance(message, Error)
        assert message.error["code"] == 400
        assert message.error["message"] == "Bad request"
    
    def test_parse_unknown_type(self):
        """Test parsing unknown message type."""
        data = {
            "type": "unknown_type",
            "data": {},
            "session_id": "session-123"
        }
        
        with pytest.raises(ValueError, match="Unsupported message type"):
            parse_message(data)
    
    def test_parse_missing_type(self):
        """Test parsing message without type."""
        data = {
            "data": {},
            "session_id": "session-123"
        }
        
        with pytest.raises(ValueError, match="Unsupported message type"):
            parse_message(data)


class TestMessageSerialization:
    """Test message serialization and deserialization."""
    
    def test_message_roundtrip(self):
        """Test message serialization and deserialization roundtrip."""
        original = UserPrompt.create("Test message", "session-123")
        
        # Serialize to dict
        data = original.model_dump()
        
        # Parse back to message
        parsed = parse_message(data)
        
        assert isinstance(parsed, UserPrompt)
        assert parsed.data["prompt"] == original.data["prompt"]
        assert parsed.session_id == original.session_id
        assert parsed.type == original.type
    
    def test_message_json_serialization(self):
        """Test message JSON serialization."""
        message = UserPrompt.create("Test message", "session-123")
        
        # Serialize to JSON
        json_str = message.model_dump_json()
        
        # Should be valid JSON
        import json
        data = json.loads(json_str)
        
        assert data["type"] == "user_prompt"
        assert data["data"]["prompt"] == "Test message"
        assert data["session_id"] == "session-123"
