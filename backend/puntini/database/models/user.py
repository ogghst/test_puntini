"""User model for authentication and user management.

This module defines the User model with authentication fields,
profile information, and relationships to roles and sessions.
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from ..base import Base


class User(Base):
    """User model for authentication and user management.
    
    Represents a user in the system with authentication credentials,
    profile information, and role assignments.
    """
    
    __tablename__ = "users"
    
    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Authentication fields
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Profile information
    full_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Account status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
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
    user_roles: Mapped[List["UserRole"]] = relationship(
        "UserRole",
        foreign_keys="UserRole.user_id",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    sessions: Mapped[List["AgentSession"]] = relationship(
        "AgentSession",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    @property
    def roles(self) -> List["Role"]:
        """Get list of roles assigned to this user.
        
        Returns:
            List of Role objects assigned to this user.
        """
        return [user_role.role for user_role in self.user_roles]
    
    @property
    def role_names(self) -> List[str]:
        """Get list of role names assigned to this user.
        
        Returns:
            List of role names assigned to this user.
        """
        return [role.name for role in self.roles]
    
    def has_role(self, role_name: str) -> bool:
        """Check if user has a specific role.
        
        Args:
            role_name: Name of the role to check.
            
        Returns:
            True if user has the role, False otherwise.
        """
        return role_name in self.role_names
    
    def has_any_role(self, role_names: List[str]) -> bool:
        """Check if user has any of the specified roles.
        
        Args:
            role_names: List of role names to check.
            
        Returns:
            True if user has any of the roles, False otherwise.
        """
        return any(role_name in self.role_names for role_name in role_names)
    
    def has_all_roles(self, role_names: List[str]) -> bool:
        """Check if user has all of the specified roles.
        
        Args:
            role_names: List of role names to check.
            
        Returns:
            True if user has all the roles, False otherwise.
        """
        return all(role_name in self.role_names for role_name in role_names)
    
    def is_admin(self) -> bool:
        """Check if user is an admin.
        
        Returns:
            True if user is admin or superuser, False otherwise.
        """
        return self.is_superuser or self.has_role("admin")
    
    def __repr__(self) -> str:
        """String representation of the user.
        
        Returns:
            String representation of the user.
        """
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"
