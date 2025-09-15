"""Message models for the WebSocket protocol.

This module defines the message structures used in the WebSocket
communication protocol as described in MESSAGING.md.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class MessageType(str, Enum):
    """Enumeration of supported message types."""
    
    # Session management
    INIT_SESSION = "init_session"
    SESSION_READY = "session_ready"
    CLOSE_SESSION = "close_session"
    
    # Chat messages
    USER_PROMPT = "user_prompt"
    ASSISTANT_RESPONSE = "assistant_response"
    
    # System messages
    REASONING = "reasoning"
    DEBUG = "debug"
    TREE_UPDATE = "tree_update"
    ERROR = "error"
    CHAT_HISTORY = "chat_history"
    
    # Heartbeat
    PING = "ping"
    PONG = "pong"


class BaseMessage(BaseModel):
    """Base message structure with common fields."""
    
    type: MessageType = Field(..., description="Message type")
    data: Dict[str, Any] = Field(default_factory=dict, description="Message payload")
    session_id: Optional[str] = Field(None, description="Session identifier")
    timestamp: Optional[str] = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="ISO timestamp for logging"
    )
    error: Optional[Dict[str, Any]] = Field(None, description="Error information if present")
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class Message(BaseMessage):
    """Generic message container."""
    pass


class InitSession(BaseMessage):
    """Initialize a new session."""
    
    type: MessageType = Field(default=MessageType.INIT_SESSION, description="Message type")
    data: Dict[str, Any] = Field(default_factory=dict, description="Empty data for init")


class SessionReady(BaseMessage):
    """Session is ready with initial state."""
    
    type: MessageType = Field(default=MessageType.SESSION_READY, description="Message type")
    data: Dict[str, Any] = Field(
        default_factory=lambda: {
            "session_id": str(uuid4()),
            "initial_tree": {},
            "status": "ready"
        },
        description="Session initialization data"
    )


class CloseSession(BaseMessage):
    """Close the current session."""
    
    type: MessageType = Field(default=MessageType.CLOSE_SESSION, description="Message type")
    data: Dict[str, Any] = Field(default_factory=dict, description="Empty data for close")


class UserPrompt(BaseMessage):
    """User chat prompt message."""
    
    type: MessageType = Field(default=MessageType.USER_PROMPT, description="Message type")
    data: Dict[str, Any] = Field(
        ...,
        description="User prompt data containing the prompt text"
    )
    
    @classmethod
    def create(cls, prompt: str, session_id: Optional[str] = None) -> "UserPrompt":
        """Create a user prompt message.
        
        Args:
            prompt: The user's prompt text.
            session_id: Optional session identifier.
            
        Returns:
            UserPrompt message instance.
        """
        return cls(
            data={"prompt": prompt},
            session_id=session_id
        )


class AssistantResponse(BaseMessage):
    """Assistant response message."""
    
    type: MessageType = Field(default=MessageType.ASSISTANT_RESPONSE, description="Message type")
    data: Dict[str, Any] = Field(
        ...,
        description="Assistant response data"
    )
    
    @classmethod
    def create(
        cls,
        text: str,
        chunk: bool = False,
        session_id: Optional[str] = None
    ) -> "AssistantResponse":
        """Create an assistant response message.
        
        Args:
            text: The response text.
            chunk: Whether this is a streaming chunk.
            session_id: Optional session identifier.
            
        Returns:
            AssistantResponse message instance.
        """
        return cls(
            data={
                "text": text,
                "chunk": chunk
            },
            session_id=session_id
        )


class Reasoning(BaseMessage):
    """Reasoning/thinking process message."""
    
    type: MessageType = Field(default=MessageType.REASONING, description="Message type")
    data: Dict[str, Any] = Field(
        ...,
        description="Reasoning data containing steps and context"
    )
    
    @classmethod
    def create(
        cls,
        steps: List[str],
        session_id: Optional[str] = None
    ) -> "Reasoning":
        """Create a reasoning message.
        
        Args:
            steps: List of reasoning steps.
            session_id: Optional session identifier.
            
        Returns:
            Reasoning message instance.
        """
        return cls(
            data={"steps": steps},
            session_id=session_id
        )


class Debug(BaseMessage):
    """Debug information message."""
    
    type: MessageType = Field(default=MessageType.DEBUG, description="Message type")
    data: Dict[str, Any] = Field(
        ...,
        description="Debug data containing message and level"
    )
    
    @classmethod
    def create(
        cls,
        message: str,
        level: str = "info",
        session_id: Optional[str] = None
    ) -> "Debug":
        """Create a debug message.
        
        Args:
            message: Debug message text.
            level: Debug level (info, warning, error).
            session_id: Optional session identifier.
            
        Returns:
            Debug message instance.
        """
        return cls(
            data={
                "message": message,
                "level": level
            },
            session_id=session_id
        )


class TreeUpdate(BaseMessage):
    """Tree structure update message."""
    
    type: MessageType = Field(default=MessageType.TREE_UPDATE, description="Message type")
    data: Dict[str, Any] = Field(
        ...,
        description="Tree update data containing delta operations"
    )
    
    @classmethod
    def create(
        cls,
        delta: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> "TreeUpdate":
        """Create a tree update message.
        
        Args:
            delta: Tree delta operation data.
            session_id: Optional session identifier.
            
        Returns:
            TreeUpdate message instance.
        """
        return cls(
            data={"delta": delta},
            session_id=session_id
        )


class Error(BaseMessage):
    """Error message."""
    
    type: MessageType = Field(default=MessageType.ERROR, description="Message type")
    data: Dict[str, Any] = Field(default_factory=dict, description="Empty data for errors")
    error: Dict[str, Any] = Field(
        ...,
        description="Error information including code and message"
    )
    
    @classmethod
    def create(
        cls,
        code: int,
        message: str,
        session_id: Optional[str] = None
    ) -> "Error":
        """Create an error message.
        
        Args:
            code: Error code.
            message: Error message.
            session_id: Optional session identifier.
            
        Returns:
            Error message instance.
        """
        return cls(
            error={
                "code": code,
                "message": message
            },
            session_id=session_id
        )


class ChatHistory(BaseMessage):
    """Chat history message."""
    
    type: MessageType = Field(default=MessageType.CHAT_HISTORY, description="Message type")
    data: Dict[str, Any] = Field(
        ...,
        description="Chat history data containing messages"
    )
    
    @classmethod
    def create(
        cls,
        messages: List[Dict[str, Any]],
        session_id: Optional[str] = None
    ) -> "ChatHistory":
        """Create a chat history message.
        
        Args:
            messages: List of chat messages.
            session_id: Optional session identifier.
            
        Returns:
            ChatHistory message instance.
        """
        return cls(
            data={"messages": messages},
            session_id=session_id
        )


class Ping(BaseMessage):
    """Ping message for heartbeat."""
    
    type: MessageType = Field(default=MessageType.PING, description="Message type")
    data: Dict[str, Any] = Field(default_factory=dict, description="Empty data for ping")


class Pong(BaseMessage):
    """Pong message for heartbeat response."""
    
    type: MessageType = Field(default=MessageType.PONG, description="Message type")
    data: Dict[str, Any] = Field(default_factory=dict, description="Empty data for pong")


# Union type for all message types
MessageUnion = Union[
    InitSession,
    SessionReady,
    CloseSession,
    UserPrompt,
    AssistantResponse,
    Reasoning,
    Debug,
    TreeUpdate,
    Error,
    ChatHistory,
    Ping,
    Pong,
]


def parse_message(data: Dict[str, Any]) -> MessageUnion:
    """Parse a message dictionary into the appropriate message type.
    
    Args:
        data: Raw message data from WebSocket.
        
    Returns:
        Parsed message instance.
        
    Raises:
        ValueError: If message type is not supported.
    """
    message_type = data.get("type")
    
    if message_type == MessageType.INIT_SESSION:
        return InitSession(**data)
    elif message_type == MessageType.SESSION_READY:
        return SessionReady(**data)
    elif message_type == MessageType.CLOSE_SESSION:
        return CloseSession(**data)
    elif message_type == MessageType.USER_PROMPT:
        return UserPrompt(**data)
    elif message_type == MessageType.ASSISTANT_RESPONSE:
        return AssistantResponse(**data)
    elif message_type == MessageType.REASONING:
        return Reasoning(**data)
    elif message_type == MessageType.DEBUG:
        return Debug(**data)
    elif message_type == MessageType.TREE_UPDATE:
        return TreeUpdate(**data)
    elif message_type == MessageType.ERROR:
        return Error(**data)
    elif message_type == MessageType.CHAT_HISTORY:
        return ChatHistory(**data)
    elif message_type == MessageType.PING:
        return Ping(**data)
    elif message_type == MessageType.PONG:
        return Pong(**data)
    else:
        raise ValueError(f"Unsupported message type: {message_type}")
