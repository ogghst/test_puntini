"""Role model for role-based access control.

This module defines the Role model for managing user roles
and permissions in the system.
"""

from datetime import datetime
from typing import List
from sqlalchemy import String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from ..base import Base


class Role(Base):
    """Role model for role-based access control.
    
    This model represents a role in the system that can be assigned
    to users for access control and permission management.
    """
    __tablename__ = "roles"
    
    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Role information
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    
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
    user_roles: Mapped[List["UserRole"]] = relationship(
        "UserRole",
        back_populates="role",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Role(id={self.id}, name='{self.name}')>"
    
    @property
    def users(self) -> List["User"]:
        """Get list of users with this role.
        
        Returns:
            List of User objects with this role.
        """
        return [user_role.user for user_role in self.user_roles]
