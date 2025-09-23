"""FastAPI application factory for the Puntini Agent API.

This module provides the main FastAPI application with REST endpoints
for authentication and WebSocket endpoints for real-time communication
as described in MESSAGING.md.
"""

import os
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.websockets import WebSocketDisconnect
from pydantic import BaseModel

from .auth import AuthManager, get_current_user, auth_manager
from .session import session_manager
from .websocket import websocket_manager
from .models import Message, UserPrompt, AssistantResponse, Error
from ..utils.settings import Settings
from ..logging import get_logger, setup_logging

from fastapi import WebSocket


class LoginRequest(BaseModel):
    """Login request model."""
    username: str
    password: str


class LoginResponse(BaseModel):
    """Login response model."""
    access_token: str
    token_type: str = "bearer"
    user_id: str


class UserResponse(BaseModel):
    """User response model."""
    username: str
    email: str
    full_name: str


class SessionStatsResponse(BaseModel):
    """Session statistics response model."""
    total_sessions: int
    active_sessions: int
    total_users: int
    session_timeout_minutes: int


class ConnectionStatsResponse(BaseModel):
    """Connection statistics response model."""
    active_connections: int
    connected_users: int
    total_sessions: int


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Get logger (logging should already be set up in create_app)
    logger = get_logger(__name__)
    
    # Startup
    logger.info("Starting Puntini Agent API...")
    
    # Start session cleanup task
    await session_manager.start_cleanup_task()
    
    logger.info("API startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Puntini Agent API...")
    
    # Stop session cleanup task
    await session_manager.stop_cleanup_task()
    
    logger.info("API shutdown complete")


def create_app(settings: Settings = None) -> FastAPI:
    """Create and configure the FastAPI application.
    
    Args:
        settings: Optional settings instance. If None, creates a new one.
        
    Returns:
        Configured FastAPI application.
    """
    if settings is None:
        settings = Settings()
    
    # Setup logging only once
    logging_service = setup_logging(settings)
    logger = get_logger(__name__)
    
    # Get server configuration
    server_config = settings.get_server_config()
    logger.info(f"Creating FastAPI app with server config: {server_config}")
    
    app = FastAPI(
        title="Puntini Agent API",
        description="Real-time messaging API for the Puntini Agent system",
        version="0.1.0",
        lifespan=lifespan,
        root_path=server_config["root_path"] if server_config["root_path"] else None,
        openapi_url=server_config["openapi_url"] if server_config["openapi_url"] else None,
        docs_url=server_config["docs_url"] if server_config["docs_url"] else None,
        redoc_url=server_config["redoc_url"] if server_config["redoc_url"] else None
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Authentication endpoints
    @app.post("/login", response_model=LoginResponse)
    async def login(request: LoginRequest):
        """Authenticate user and return JWT token."""
        auth_logger = get_logger("puntini.api.auth")
        auth_logger.info(f"Login attempt for user: {request.username}")
        
        user = auth_manager.authenticate_user(request.username, request.password)
        if not user:
            auth_logger.warning(f"Failed login attempt for user: {request.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token = auth_manager.create_access_token(data={"sub": user["username"]})
        auth_logger.info(f"Successful login for user: {request.username}")
        
        return LoginResponse(
            access_token=access_token,
            user_id=user["username"]
        )
    
    @app.post("/register", response_model=UserResponse)
    async def register(request: LoginRequest):
        """Register a new user."""
        auth_logger = get_logger("puntini.api.auth")
        auth_logger.info(f"Registration attempt for user: {request.username}")
        
        try:
            user = auth_manager.create_user(
                username=request.username,
                password=request.password,
                email=f"{request.username}@example.com",  # Default email
                full_name=request.username.title()
            )
            auth_logger.info(f"Successful registration for user: {request.username}")
            return UserResponse(
                username=user["username"],
                email=user["email"],
                full_name=user["full_name"]
            )
        except ValueError as e:
            auth_logger.warning(f"Failed registration for user: {request.username} - {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    
    @app.get("/me", response_model=UserResponse)
    async def get_current_user_info(current_user: str = Depends(get_current_user)):
        """Get current user information."""
        user = auth_manager.get_user(current_user)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse(
            username=user["username"],
            email=user["email"],
            full_name=user["full_name"]
        )
    
    # Session management endpoints
    @app.get("/sessions/stats", response_model=SessionStatsResponse)
    async def get_session_stats(current_user: str = Depends(get_current_user)):
        """Get session statistics."""
        stats = session_manager.get_stats()
        return SessionStatsResponse(**stats)
    
    @app.get("/sessions/my", response_model=Dict[str, Any])
    async def get_my_sessions(current_user: str = Depends(get_current_user)):
        """Get current user's sessions."""
        sessions = session_manager.get_user_sessions(current_user)
        return {
            "sessions": [session.to_dict() for session in sessions]
        }
    
    # WebSocket connection statistics
    @app.get("/connections/stats", response_model=ConnectionStatsResponse)
    async def get_connection_stats(current_user: str = Depends(get_current_user)):
        """Get WebSocket connection statistics."""
        stats = websocket_manager.get_connection_stats()
        return ConnectionStatsResponse(**stats)
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "agent_available": websocket_manager.agent is not None,
            "session_manager": "active",
            "websocket_manager": "active"
        }
    
    # WebSocket endpoint
    @app.websocket("/ws/chat")
    async def websocket_chat(websocket: WebSocket, token: str = None):
        """WebSocket endpoint for real-time chat."""
        ws_logger = get_logger("puntini.api.websocket")
        
        if not token:
            ws_logger.warning("WebSocket connection attempt without token")
            await websocket.close(code=1008, reason="Missing token")
            return
        
        ws_logger.info(f"WebSocket connection attempt with token: {token[:10]}...")
        
        # Connect to WebSocket manager (this will accept the connection)
        session_id = await websocket_manager.connect(websocket, token)
        if not session_id:
            ws_logger.warning("Failed to establish WebSocket connection")
            return
        
        ws_logger.info(f"WebSocket connection established with session: {session_id}")
        
        try:
            while True:
                # Receive message
                data = await websocket.receive_text()
                ws_logger.debug(f"Received WebSocket message for session {session_id}: {data[:100]}...")
                
                try:
                    import json
                    message_data = json.loads(data)
                except json.JSONDecodeError:
                    ws_logger.warning(f"Invalid JSON received from session {session_id}")
                    # Send error for invalid JSON
                    error_message = Error.create(
                        code=400,
                        message="Invalid JSON format",
                        session_id=session_id
                    )
                    await websocket_manager.send_message(session_id, error_message)
                    continue
                
                # Handle message
                await websocket_manager.handle_message(session_id, message_data)
                
        except WebSocketDisconnect:
            ws_logger.info(f"WebSocket disconnected for session: {session_id}")
            await websocket_manager.disconnect(session_id)
        except Exception as e:
            ws_logger.error(f"WebSocket error for session {session_id}: {e}")
            await websocket_manager.disconnect(session_id)
    
    return app


def run_server(settings: Settings = None):
    """Run the FastAPI server with configuration from settings.
    
    Args:
        settings: Optional settings instance. If None, creates a new one.
    """
    import uvicorn
    
    if settings is None:
        settings = Settings()
    
    # Get server configuration
    server_config = settings.get_server_config()
    
    print(f"Starting Puntini Agent API on {server_config['host']}:{server_config['port']}")
    print(f"Server configuration: {server_config}")
    
    # Create the application instance
    app_instance = create_app(settings)
    
    # Run the server
    uvicorn.run(
        app_instance,
        host=server_config["host"],
        port=server_config["port"],
        reload=server_config["reload"],
        workers=server_config["workers"],
        access_log=server_config["access_log"],
        log_level=server_config["log_level"]
    )


# Create the application instance
app = create_app()


if __name__ == "__main__":
    # Run the server when this module is executed directly
    run_server()
