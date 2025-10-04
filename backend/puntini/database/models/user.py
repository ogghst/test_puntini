"""User model for authentication and user management.

This module defines the User model with authentication fields,
role management, and user profile information.
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from ..base import Base


class User(Base):
    """User model for authentication and user management.
    
    This model represents a user in the system with authentication
    capabilities, role management, and profile information.
    """
    __tablename__ = "users"
    
    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Authentication fields
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # User status and permissions
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Profile information
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
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
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Relationships
    sessions: Mapped[List["Session"]] = relationship(
        "Session",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    user_roles: Mapped[List["UserRole"]] = relationship(
        "UserRole",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"
    
    @property
    def roles(self) -> List[str]:
        """Get list of role names for this user.
        
        Returns:
            List of role names.
        """
        return [user_role.role.name for user_role in self.user_roles]
    
    def has_role(self, role_name: str) -> bool:
        """Check if user has a specific role.
        
        Args:
            role_name: Name of the role to check.
            
        Returns:
            True if user has the role, False otherwise.
        """
        return role_name in self.roles
    
    def is_admin_user(self) -> bool:
        """Check if user is an admin.
        
        Returns:
            True if user is admin, False otherwise.
        """
        return self.is_admin or self.has_role("admin")
