"""WebSocket management module for real-time communication.

This module provides WebSocket connection management and message
handling for the Puntini Agent system as described in MESSAGING.md.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4
import uuid

from fastapi import WebSocket, WebSocketDisconnect
from langfuse.langchain import CallbackHandler
from langfuse import Langfuse
from langfuse import get_client
from langgraph.graph import StateGraph

from ..logging import get_logger

from puntini.utils.settings import settings

from .auth import get_current_user_websocket
from .models import (
    Message,
    MessageType,
    UserPrompt,
    AssistantResponse,
    Reasoning,
    Debug,
    
    Error,
    SessionReady,
    InitSession,
    CloseSession,
    ChatHistory,
    Ping,
    Pong,
    parse_message,
)
from .session import SessionManager, session_manager
from ..agents.agent_factory import create_simple_agent, create_agent_with_components
from ..graph.graph_store_factory import create_memory_graph_store
from ..context.context_manager_factory import create_simple_context_manager
from ..tools.tool_setup import create_configured_tool_registry
from ..observability.tracer_factory import create_console_tracer


class WebSocketManager:
    """Manages WebSocket connections and message routing."""
    
    def __init__(self, session_manager: SessionManager):
        """Initialize the WebSocket manager.
        
        Args:
            session_manager: Session manager instance.
        """
        self.session_manager = session_manager
        self.active_connections: Dict[str, WebSocket] = {}  # session_id -> websocket
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> set of session_ids
        self.agent: StateGraph = None
        self.logger = get_logger(__name__)
        self._initialize_agent()
    
    def _initialize_agent(self) -> None:
        """Initialize the LangGraph agent with components."""
        try:
            # Create agent components
            graph_store = create_memory_graph_store()
            context_manager = create_simple_context_manager()
            tool_registry = create_configured_tool_registry()
            tracer = create_console_tracer()
            
            # Create the agent with components
            self.agent = create_agent_with_components(
                graph_store=graph_store,
                context_manager=context_manager,
                tool_registry=tool_registry,
                tracer=tracer
            )
            
            self.logger.info("Agent initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize agent: {e}")
            self.agent = None
    
    async def connect(self, websocket: WebSocket, token: str) -> Optional[str]:
        """Handle new WebSocket connection.
        
        Args:
            websocket: WebSocket connection.
            token: JWT authentication token.
            
        Returns:
            Session ID if connection successful, None otherwise.
        """
        # Authenticate user
        user_id = await get_current_user_websocket(token)
        if not user_id:
            self.logger.warning(f"WebSocket connection attempt with invalid token: {token[:10]}...")
            await websocket.close(code=1008, reason="Invalid token")
            return None
        
        # Accept connection
        await websocket.accept()
        
        # Create new session
        session_data = self.session_manager.create_session(user_id)
        session_id = session_data.session_id
        
        # Store connection
        self.active_connections[session_id] = websocket
        
        # Track user connections
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(session_id)
        
        self.logger.info(f"WebSocket connected: user={user_id}, session={session_id}")
        return session_id
    
    async def disconnect(self, session_id: str) -> None:
        """Handle WebSocket disconnection.
        
        Args:
            session_id: Session identifier.
        """
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            del self.active_connections[session_id]
            
            # Find user_id for this session
            user_id = None
            for uid, sessions in self.user_connections.items():
                if session_id in sessions:
                    user_id = uid
                    sessions.remove(session_id)
                    if not sessions:
                        del self.user_connections[uid]
                    break
            
            # Close session
            self.session_manager.close_session(session_id)
            
            self.logger.info(f"WebSocket disconnected: user={user_id}, session={session_id}")
    
    async def send_message(self, session_id: str, message: Message) -> bool:
        """Send a message to a specific session.
        
        Args:
            session_id: Session identifier.
            message: Message to send.
            
        Returns:
            True if message was sent, False if connection not found.
        """
        websocket = self.active_connections.get(session_id)
        if not websocket:
            return False
        
        try:
            await websocket.send_text(message.model_dump_json())
            self.logger.debug(f"Message sent to session {session_id}: {message.type} - {message.model_dump_json()}")
            return True
        except Exception as e:
            self.logger.error(f"Error sending message to {session_id}: {e}")
            return False
    
    async def send_to_user(self, user_id: str, message: Message) -> int:
        """Send a message to all sessions of a user.
        
        Args:
            user_id: User identifier.
            message: Message to send.
            
        Returns:
            Number of sessions the message was sent to.
        """
        session_ids = self.user_connections.get(user_id, set())
        sent_count = 0
        
        for session_id in list(session_ids):  # Copy to avoid modification during iteration
            if await self.send_message(session_id, message):
                sent_count += 1
            else:
                # Connection is dead, clean up
                await self.disconnect(session_id)
        
        return sent_count
    
    async def handle_message(self, session_id: str, message_data: Dict[str, Any]) -> None:
        """Handle incoming WebSocket message.
        
        Args:
            session_id: Session identifier.
            message_data: Raw message data.
        """
        try:
            message = parse_message(message_data)
            self.logger.debug(f"Processing message for session {session_id}: {message.type}")
            await self._process_message(session_id, message)
        except Exception as e:
            self.logger.error(f"Error handling message for session {session_id}: {e}")
            error_message = Error.create(
                code=400,
                message=f"Invalid message format: {str(e)}",
                session_id=session_id
            )
            await self.send_message(session_id, error_message)
    
    async def _process_message(self, session_id: str, message: Message) -> None:
        """Process a parsed message.
        
        Args:
            session_id: Session identifier.
            message: Parsed message.
        """
        if message.type == MessageType.INIT_SESSION:
            await self._handle_init_session(session_id, message)
        elif message.type == MessageType.USER_PROMPT:
            await self._handle_user_prompt(session_id, message)
        elif message.type == MessageType.CLOSE_SESSION:
            await self._handle_close_session(session_id, message)
        elif message.type == MessageType.PING:
            await self._handle_ping(session_id, message)
        else:
            # Unknown message type
            error_message = Error.create(
                code=400,
                message=f"Unknown message type: {message.type}",
                session_id=session_id
            )
            await self.send_message(session_id, error_message)
    
    async def _handle_init_session(self, session_id: str, message: InitSession) -> None:
        """Handle session initialization.
        
        Args:
            session_id: Session identifier.
            message: Init session message.
        """
        session_data = self.session_manager.get_session(session_id)
        if not session_data:
            error_message = Error.create(
                code=404,
                message="Session not found",
                session_id=session_id
            )
            await self.send_message(session_id, error_message)
            return
        
        # Send session ready message
        ready_message = SessionReady(
            data={
                "session_id": session_id,
                "initial_graph": session_data.graph_data,
                "status": "ready"
            },
            session_id=session_id
        )
        await self.send_message(session_id, ready_message)
    
    async def _handle_user_prompt(self, session_id: str, message: UserPrompt) -> None:
        """Handle user prompt message.
        
        Args:
            session_id: Session identifier.
            message: User prompt message.
        """
        session_data = self.session_manager.get_session(session_id)
        if not session_data:
            error_message = Error.create(
                code=404,
                message="Session not found",
                session_id=session_id
            )
            await self.send_message(session_id, error_message)
            return
        
        # Add message to chat history
        self.session_manager.add_message(session_id, {
            "role": "user",
            "content": message.data.get("prompt", ""),
            "type": "user_prompt"
        })
        
        # Process with agent if available
        if self.agent:
            self.logger.info(f"Processing user prompt with agent for session {session_id}")
            await self._process_with_agent(session_id, message)
        else:
            self.logger.warning(f"Agent not available, sending fallback response for session {session_id}")
            # Fallback response
            response = AssistantResponse.create(
                text="I'm sorry, the agent is not available at the moment.",
                session_id=session_id
            )
            await self.send_message(session_id, response)
    
    async def _process_with_agent(self, session_id: str, message: UserPrompt) -> None:
        """Process user prompt with the LangGraph agent.
        
        Args:
            session_id: Session identifier.
            message: User prompt message.
        """
        try:
            # Send reasoning message
            reasoning = Reasoning.create(
                steps=[
                    "Received user prompt",
                    "Processing with LangGraph agent",
                    "Generating response"
                ],
                session_id=session_id
            )
            await self.send_message(session_id, reasoning)
            
            # Create initial state for agent
            from ..orchestration.state import State
            from ..agents.agent_factory import create_initial_state
            
            # Get components from the agent
            components = getattr(self.agent, '_components', {})
            graph_store = components.get('graph_store')
            context_manager = components.get('context_manager')
            tool_registry = components.get('tool_registry')
            tracer = components.get('tracer')
            
            if not all([graph_store, context_manager, tool_registry, tracer]):
                raise ValueError("Agent components not properly initialized")
            
            # Create LLM for the graph context (like in CLI)
            from ..llm.llm_models import LLMFactory
            llm_factory = LLMFactory()
            llm = llm_factory.get_default_llm()
            
            # Create initial state
            initial_state = create_initial_state(
                goal=message.data.get("prompt", ""),
                graph_store=graph_store,
                context_manager=context_manager,
                tool_registry=tool_registry,
                tracer=tracer
            )
            
            Langfuse(
                secret_key=settings.langfuse.secret_key,
                public_key=settings.langfuse.public_key,
                host=settings.langfuse.host
            )   
            langfuse = get_client()
            langfuse_handler = CallbackHandler()
            thread_id = str(uuid.uuid4())
                
            # Pass LLM and components through context (like in CLI)
            context = {
                "llm": llm,
                "graph_store": graph_store,
                "context_manager": context_manager,
                "tool_registry": tool_registry,
                "tracer": tracer
            }
            
            config = {
                "configurable": {"thread_id": str(uuid.uuid4())}, 
                "callbacks": [langfuse_handler],
                "recursion_limit": 100  # Increase from default 25 to 100
            }
            
            # Stream agent execution with context
            async for chunk in self.agent.astream(initial_state, stream_mode=["updates", "custom", "events", "messages-tuple"], context=context, config=config):
                await self._handle_agent_chunk(session_id, chunk)
            
            # Send completion message
            completion = AssistantResponse.create(
                text="Agent processing completed.",
                session_id=session_id
            )
            await self.send_message(session_id, completion)
            
        except Exception as e:
            self.logger.error(f"Error processing with agent for session {session_id}: {e}")
            error_message = Error.create(
                code=500,
                message=f"Agent processing error: {str(e)}",
                session_id=session_id
            )
            await self.send_message(session_id, error_message)
    
    async def _handle_agent_chunk(self, session_id: str, chunk: Any) -> None:
        """Handle a chunk from agent streaming.
        
        Args:
            session_id: Session identifier.
            chunk: Agent streaming chunk.
        """
        
        self.logger.info(f"Agent chunk: {chunk}")
        
        try:
            if isinstance(chunk, tuple) and len(chunk) == 2:
                mode, data = chunk
                
                if mode == "updates":
                    # Handle state updates
                    await self._handle_state_update(session_id, data)
                elif mode == "custom":
                    # Handle custom data
                    await self._handle_custom_data(session_id, data)
            else:
                # Handle single chunk
                await self._handle_single_chunk(session_id, chunk)
                
        except Exception as e:
            self.logger.error(f"Error handling agent chunk for session {session_id}: {e}")
    
    async def _handle_state_update(self, session_id: str, data: Dict[str, Any]) -> None:
        """Handle agent state update.
        
        Args:
            session_id: Session identifier.
            data: State update data.
        """
        # Send debug message about state update
        debug = Debug.create(
            message=f"Agent state updated: {list(data.keys())}",
            level="info",
            session_id=session_id
        )
        await self.send_message(session_id, debug)
    
    async def _handle_custom_data(self, session_id: str, data: Dict[str, Any]) -> None:
        """Handle custom data from agent.
        
        Args:
            session_id: Session identifier.
            data: Custom data.
        """
        # Send as debug message
        debug = Debug.create(
            message=f"Agent custom data: {data}",
            level="info",
            session_id=session_id
        )
        await self.send_message(session_id, debug)
    
    async def _handle_single_chunk(self, session_id: str, chunk: Any) -> None:
        """Handle single chunk from agent.
        
        Args:
            session_id: Session identifier.
            chunk: Single chunk data.
        """
        # Send as debug message
        debug = Debug.create(
            message=f"Agent chunk: {str(chunk)[:100]}...",
            level="info",
            session_id=session_id
        )
        await self.send_message(session_id, debug)
    
    async def _handle_close_session(self, session_id: str, message: CloseSession) -> None:
        """Handle session close.
        
        Args:
            session_id: Session identifier.
            message: Close session message.
        """
        await self.disconnect(session_id)
    
    async def _handle_ping(self, session_id: str, message: Ping) -> None:
        """Handle ping message.
        
        Args:
            session_id: Session identifier.
            message: Ping message.
        """
        pong = Pong(session_id=session_id)
        await self.send_message(session_id, pong)
    
    async def broadcast_to_all(self, message: Message) -> int:
        """Broadcast a message to all active connections.
        
        Args:
            message: Message to broadcast.
            
        Returns:
            Number of connections the message was sent to.
        """
        sent_count = 0
        for session_id in list(self.active_connections.keys()):
            if await self.send_message(session_id, message):
                sent_count += 1
            else:
                # Connection is dead, clean up
                await self.disconnect(session_id)
        
        return sent_count
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get WebSocket connection statistics.
        
        Returns:
            Dictionary with connection statistics.
        """
        return {
            "active_connections": len(self.active_connections),
            "connected_users": len(self.user_connections),
            "total_sessions": sum(len(sessions) for sessions in self.user_connections.values())
        }


# Global WebSocket manager instance
websocket_manager = WebSocketManager(session_manager)
