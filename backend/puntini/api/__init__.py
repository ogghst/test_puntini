"""API module for Puntini Agent messaging system.

This module provides FastAPI-based REST and WebSocket endpoints for
real-time communication with the Puntini Agent system, supporting
multi-user sessions, authentication, and streaming capabilities.
"""

from .app import create_app
from .auth import AuthManager, get_current_user
from .session import SessionManager
from .websocket import WebSocketManager
from .models import (
    Message,
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
)

__all__ = [
    # Main app factory
    "create_app",
    
    # Authentication
    "AuthManager",
    "get_current_user",
    
    # Session management
    "SessionManager",
    
    # WebSocket management
    "WebSocketManager",
    
    # Message models
    "Message",
    "MessageType",
    "UserPrompt",
    "AssistantResponse",
    "Reasoning",
    "Debug",
    "GraphUpdate",
    "Error",
    "SessionReady",
    "InitSession",
    "CloseSession",
    "ChatHistory",
    "Ping",
    "Pong",
]
