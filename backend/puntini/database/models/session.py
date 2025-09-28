"""Agent session model for session persistence.

This module defines the AgentSession model for persisting agent
session data and enabling session recovery.
"""

from datetime import datetime
from typing import Optional, Dict, Any, TYPE_CHECKING
from sqlalchemy import String, DateTime, Text, ForeignKey, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from ..base import Base

if TYPE_CHECKING:
    from .user import User


class AgentSession(Base):
    """Agent session model for session persistence.
    
    Represents an agent session that can be persisted and recovered,
    allowing users to resume their agent interactions across sessions.
    """
    
    __tablename__ = "agent_sessions"
    
    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Session identification
    session_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Session metadata
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Session state
    current_step: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    goal: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    progress: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    failures: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    artifacts: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    
    # Session status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_paused: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    
    # Session context
    context_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    escalation_context: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    last_activity: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="sessions")
    
    def get_progress(self) -> list:
        """Get progress as a list.
        
        Returns:
            List of progress items.
        """
        if not self.progress:
            return []
        
        import json
        try:
            return json.loads(self.progress)
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_progress(self, progress: list) -> None:
        """Set progress from a list.
        
        Args:
            progress: List of progress items.
        """
        import json
        self.progress = json.dumps(progress)
    
    def get_failures(self) -> list:
        """Get failures as a list.
        
        Returns:
            List of failure items.
        """
        if not self.failures:
            return []
        
        import json
        try:
            return json.loads(self.failures)
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_failures(self, failures: list) -> None:
        """Set failures from a list.
        
        Args:
            failures: List of failure items.
        """
        import json
        self.failures = json.dumps(failures)
    
    def get_artifacts(self) -> list:
        """Get artifacts as a list.
        
        Returns:
            List of artifact items.
        """
        if not self.artifacts:
            return []
        
        import json
        try:
            return json.loads(self.artifacts)
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_artifacts(self, artifacts: list) -> None:
        """Set artifacts from a list.
        
        Args:
            artifacts: List of artifact items.
        """
        import json
        self.artifacts = json.dumps(artifacts)
    
    def get_context_data(self) -> Dict[str, Any]:
        """Get context data as a dictionary.
        
        Returns:
            Dictionary of context data.
        """
        if not self.context_data:
            return {}
        
        import json
        try:
            return json.loads(self.context_data)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_context_data(self, context_data: Dict[str, Any]) -> None:
        """Set context data from a dictionary.
        
        Args:
            context_data: Dictionary of context data.
        """
        import json
        self.context_data = json.dumps(context_data)
    
    def get_escalation_context(self) -> Dict[str, Any]:
        """Get escalation context as a dictionary.
        
        Returns:
            Dictionary of escalation context.
        """
        if not self.escalation_context:
            return {}
        
        import json
        try:
            return json.loads(self.escalation_context)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_escalation_context(self, escalation_context: Dict[str, Any]) -> None:
        """Set escalation context from a dictionary.
        
        Args:
            escalation_context: Dictionary of escalation context.
        """
        import json
        self.escalation_context = json.dumps(escalation_context)
    
    def is_expired(self, timeout_hours: int = 24) -> bool:
        """Check if session is expired.
        
        Args:
            timeout_hours: Hours after which session expires.
            
        Returns:
            True if session is expired, False otherwise.
        """
        if not self.last_activity:
            return False
        
        from datetime import timedelta
        expiry_time = self.last_activity + timedelta(hours=timeout_hours)
        return datetime.utcnow() > expiry_time
    
    def update_activity(self) -> None:
        """Update the last activity timestamp."""
        self.last_activity = datetime.utcnow()
    
    def __repr__(self) -> str:
        """String representation of the agent session.
        
        Returns:
            String representation of the agent session.
        """
        return f"<AgentSession(id={self.id}, session_id='{self.session_id}', user_id={self.user_id}, is_active={self.is_active})>"
