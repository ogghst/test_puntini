"""Session model for agent state persistence.

This module defines the Session model for persisting agent
session data and enabling session recovery.
"""

from datetime import datetime
from typing import Optional, Dict, Any, TYPE_CHECKING
from sqlalchemy import ForeignKey, DateTime, Text, String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import JSON

from ..base import Base

if TYPE_CHECKING:
    from .user import User


class Session(Base):
    """Session model for agent state persistence.
    
    This model represents an agent session with state data,
    enabling session recovery and persistence across browser refreshes.
    """
    __tablename__ = "sessions"
    
    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Foreign key to user
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Session information
    session_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Session state data (JSON)
    state_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    
    # Session metadata
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    thread_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    
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
    last_accessed: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="sessions")
    
    def __repr__(self) -> str:
        return f"<Session(id={self.id}, user_id={self.user_id}, name='{self.session_name}')>"
    
    def is_expired(self) -> bool:
        """Check if session is expired.
        
        Returns:
            True if session is expired, False otherwise.
        """
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    def update_last_accessed(self):
        """Update the last accessed timestamp."""
        self.last_accessed = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary.
        
        Returns:
            Dictionary representation of the session.
        """
        return {
            "id": self.id,
            "user_id": self.user_id,
            "session_name": self.session_name,
            "description": self.description,
            "state_data": self.state_data,
            "is_active": self.is_active,
            "thread_id": self.thread_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }
