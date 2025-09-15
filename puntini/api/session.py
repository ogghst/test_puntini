"""Session management module for multi-user support.

This module provides in-memory session management for tracking
active WebSocket connections and session data as described in MESSAGING.md.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from ..utils.settings import Settings


class SessionData:
    """Represents session data for a user."""
    
    def __init__(
        self,
        session_id: str,
        user_id: str,
        tree_data: Optional[Dict[str, Any]] = None,
        chat_history: Optional[List[Dict[str, Any]]] = None,
        created_at: Optional[datetime] = None
    ):
        """Initialize session data.
        
        Args:
            session_id: Unique session identifier.
            user_id: User identifier.
            tree_data: Current tree state.
            chat_history: Chat message history.
            created_at: Session creation timestamp.
        """
        self.session_id = session_id
        self.user_id = user_id
        self.tree_data = tree_data or {}
        self.chat_history = chat_history or []
        self.created_at = created_at or datetime.utcnow()
        self.last_activity = datetime.utcnow()
        self.is_active = True
    
    def update_activity(self) -> None:
        """Update the last activity timestamp."""
        self.last_activity = datetime.utcnow()
    
    def add_message(self, message: Dict[str, Any]) -> None:
        """Add a message to chat history.
        
        Args:
            message: Message data to add.
        """
        self.chat_history.append({
            **message,
            "timestamp": datetime.utcnow().isoformat()
        })
        self.update_activity()
    
    def update_tree(self, tree_delta: Dict[str, Any]) -> None:
        """Update tree data with a delta.
        
        Args:
            tree_delta: Tree delta operation data.
        """
        # Apply delta to tree data
        action = tree_delta.get("action")
        if action == "add":
            self._apply_add_delta(tree_delta)
        elif action == "update":
            self._apply_update_delta(tree_delta)
        elif action == "delete":
            self._apply_delete_delta(tree_delta)
        
        self.update_activity()
    
    def _apply_add_delta(self, delta: Dict[str, Any]) -> None:
        """Apply an add delta to tree data.
        
        Args:
            delta: Add delta operation.
        """
        path = delta.get("path", "/")
        node = delta.get("node", {})
        
        if path == "/":
            if "children" not in self.tree_data:
                self.tree_data["children"] = []
            self.tree_data["children"].append(node)
        else:
            # Navigate to path and add node
            self._navigate_and_add(path, node)
    
    def _apply_update_delta(self, delta: Dict[str, Any]) -> None:
        """Apply an update delta to tree data.
        
        Args:
            delta: Update delta operation.
        """
        path = delta.get("path", "/")
        updates = delta.get("updates", {})
        
        # Navigate to path and update
        self._navigate_and_update(path, updates)
    
    def _apply_delete_delta(self, delta: Dict[str, Any]) -> None:
        """Apply a delete delta to tree data.
        
        Args:
            delta: Delete delta operation.
        """
        path = delta.get("path", "/")
        node_id = delta.get("node_id")
        
        # Navigate to path and delete node
        self._navigate_and_delete(path, node_id)
    
    def _navigate_and_add(self, path: str, node: Dict[str, Any]) -> None:
        """Navigate to path and add node.
        
        Args:
            path: Path to navigate to.
            node: Node to add.
        """
        # Simple implementation - in production, implement proper path navigation
        if "children" not in self.tree_data:
            self.tree_data["children"] = []
        self.tree_data["children"].append(node)
    
    def _navigate_and_update(self, path: str, updates: Dict[str, Any]) -> None:
        """Navigate to path and update node.
        
        Args:
            path: Path to navigate to.
            updates: Updates to apply.
        """
        # Simple implementation - in production, implement proper path navigation
        if path == "/":
            self.tree_data.update(updates)
    
    def _navigate_and_delete(self, path: str, node_id: str) -> None:
        """Navigate to path and delete node.
        
        Args:
            path: Path to navigate to.
            node_id: ID of node to delete.
        """
        # Simple implementation - in production, implement proper path navigation
        if "children" in self.tree_data:
            self.tree_data["children"] = [
                child for child in self.tree_data["children"]
                if child.get("id") != node_id
            ]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session data to dictionary.
        
        Returns:
            Dictionary representation of session data.
        """
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "tree_data": self.tree_data,
            "chat_history": self.chat_history,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "is_active": self.is_active
        }


class SessionManager:
    """Manages user sessions and WebSocket connections."""
    
    def __init__(self, settings: Optional[Settings] = None):
        """Initialize the session manager.
        
        Args:
            settings: Optional settings instance. If None, creates a new one.
        """
        self.settings = settings or Settings()
        self.sessions: Dict[str, SessionData] = {}
        self.user_sessions: Dict[str, List[str]] = {}  # user_id -> list of session_ids
        self.session_timeout = timedelta(hours=1)  # 1 hour timeout
        self._cleanup_task: Optional[asyncio.Task] = None
    
    def create_session(self, user_id: str) -> SessionData:
        """Create a new session for a user.
        
        Args:
            user_id: User identifier.
            
        Returns:
            Created session data.
        """
        session_id = str(uuid4())
        session_data = SessionData(
            session_id=session_id,
            user_id=user_id
        )
        
        self.sessions[session_id] = session_data
        
        # Track user sessions
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = []
        self.user_sessions[user_id].append(session_id)
        
        return session_data
    
    def get_session(self, session_id: str) -> Optional[SessionData]:
        """Get session data by session ID.
        
        Args:
            session_id: Session identifier.
            
        Returns:
            Session data if found, None otherwise.
        """
        session = self.sessions.get(session_id)
        if session:
            session.update_activity()
        return session
    
    def get_user_sessions(self, user_id: str) -> List[SessionData]:
        """Get all sessions for a user.
        
        Args:
            user_id: User identifier.
            
        Returns:
            List of session data for the user.
        """
        session_ids = self.user_sessions.get(user_id, [])
        sessions = []
        for session_id in session_ids:
            session = self.sessions.get(session_id)
            if session and session.is_active:
                sessions.append(session)
        return sessions
    
    def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """Update session data.
        
        Args:
            session_id: Session identifier.
            updates: Updates to apply.
            
        Returns:
            True if session was updated, False if not found.
        """
        session = self.sessions.get(session_id)
        if not session:
            return False
        
        if "tree_data" in updates:
            session.tree_data = updates["tree_data"]
        if "chat_history" in updates:
            session.chat_history = updates["chat_history"]
        
        session.update_activity()
        return True
    
    def add_message(self, session_id: str, message: Dict[str, Any]) -> bool:
        """Add a message to session chat history.
        
        Args:
            session_id: Session identifier.
            message: Message data to add.
            
        Returns:
            True if message was added, False if session not found.
        """
        session = self.sessions.get(session_id)
        if not session:
            return False
        
        session.add_message(message)
        return True
    
    def update_tree(self, session_id: str, tree_delta: Dict[str, Any]) -> bool:
        """Update session tree data with delta.
        
        Args:
            session_id: Session identifier.
            tree_delta: Tree delta operation.
            
        Returns:
            True if tree was updated, False if session not found.
        """
        session = self.sessions.get(session_id)
        if not session:
            return False
        
        session.update_tree(tree_delta)
        return True
    
    def close_session(self, session_id: str) -> bool:
        """Close a session.
        
        Args:
            session_id: Session identifier.
            
        Returns:
            True if session was closed, False if not found.
        """
        session = self.sessions.get(session_id)
        if not session:
            return False
        
        session.is_active = False
        
        # Remove from user sessions
        user_id = session.user_id
        if user_id in self.user_sessions:
            self.user_sessions[user_id] = [
                sid for sid in self.user_sessions[user_id] if sid != session_id
            ]
            if not self.user_sessions[user_id]:
                del self.user_sessions[user_id]
        
        # Remove from sessions
        del self.sessions[session_id]
        return True
    
    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions.
        
        Returns:
            Number of sessions cleaned up.
        """
        now = datetime.utcnow()
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            if now - session.last_activity > self.session_timeout:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            self.close_session(session_id)
        
        return len(expired_sessions)
    
    async def start_cleanup_task(self) -> None:
        """Start the cleanup task for expired sessions."""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def stop_cleanup_task(self) -> None:
        """Stop the cleanup task."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
    
    async def _cleanup_loop(self) -> None:
        """Cleanup loop that runs periodically."""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                cleaned = self.cleanup_expired_sessions()
                if cleaned > 0:
                    print(f"Cleaned up {cleaned} expired sessions")
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in cleanup loop: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get session manager statistics.
        
        Returns:
            Dictionary with session statistics.
        """
        active_sessions = sum(1 for s in self.sessions.values() if s.is_active)
        total_users = len(self.user_sessions)
        
        return {
            "total_sessions": len(self.sessions),
            "active_sessions": active_sessions,
            "total_users": total_users,
            "session_timeout_minutes": int(self.session_timeout.total_seconds() / 60)
        }


# Global session manager instance
session_manager = SessionManager()
