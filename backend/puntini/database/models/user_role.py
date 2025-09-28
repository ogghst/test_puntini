"""User-Role association model.

This module defines the UserRole model for the many-to-many
relationship between users and roles.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import ForeignKey, DateTime, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from ..base import Base


class UserRole(Base):
    """User-Role association model.
    
    Represents the many-to-many relationship between users and roles,
    allowing users to have multiple roles and roles to be assigned
    to multiple users.
    """
    
    __tablename__ = "user_roles"
    
    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Foreign keys
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    role_id: Mapped[int] = mapped_column(
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Association properties
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    assigned_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=True
    )
    
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
    
    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], back_populates="user_roles")
    role: Mapped["Role"] = relationship("Role", back_populates="user_roles")
    assigned_by_user: Mapped[Optional["User"]] = relationship(
        "User", 
        foreign_keys=[assigned_by]
    )
    
    # Unique constraint to prevent duplicate assignments
    __table_args__ = (
        UniqueConstraint('user_id', 'role_id', name='uq_user_role'),
    )
    
    def __repr__(self) -> str:
        """String representation of the user-role association.
        
        Returns:
            String representation of the user-role association.
        """
        return f"<UserRole(user_id={self.user_id}, role_id={self.role_id}, is_active={self.is_active})>"
