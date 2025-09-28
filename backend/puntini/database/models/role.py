"""Role model for role-based access control.

This module defines the Role model for implementing role-based
access control (RBAC) in the application.
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, DateTime, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from ..base import Base


class Role(Base):
    """Role model for role-based access control.
    
    Represents a role in the system that can be assigned to users
    to control access to different features and resources.
    """
    
    __tablename__ = "roles"
    
    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Role identification
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Role properties
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_system_role: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    priority: Mapped[int] = mapped_column(default=0, nullable=False)  # Higher priority = more permissions
    
    # Permissions (stored as JSON string for flexibility)
    permissions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
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
    
    @property
    def users(self) -> List["User"]:
        """Get list of users assigned to this role.
        
        Returns:
            List of User objects assigned to this role.
        """
        return [user_role.user for user_role in self.user_roles]
    
    @property
    def user_count(self) -> int:
        """Get number of users assigned to this role.
        
        Returns:
            Number of users assigned to this role.
        """
        return len(self.user_roles)
    
    def has_permission(self, permission: str) -> bool:
        """Check if role has a specific permission.
        
        Args:
            permission: Permission to check.
            
        Returns:
            True if role has the permission, False otherwise.
        """
        if not self.permissions:
            return False
        
        # Parse permissions from JSON string
        import json
        try:
            permissions_list = json.loads(self.permissions)
            return permission in permissions_list
        except (json.JSONDecodeError, TypeError):
            return False
    
    def add_permission(self, permission: str) -> None:
        """Add a permission to the role.
        
        Args:
            permission: Permission to add.
        """
        import json
        
        # Parse existing permissions
        permissions_list = []
        if self.permissions:
            try:
                permissions_list = json.loads(self.permissions)
            except (json.JSONDecodeError, TypeError):
                permissions_list = []
        
        # Add permission if not already present
        if permission not in permissions_list:
            permissions_list.append(permission)
            self.permissions = json.dumps(permissions_list)
    
    def remove_permission(self, permission: str) -> None:
        """Remove a permission from the role.
        
        Args:
            permission: Permission to remove.
        """
        import json
        
        # Parse existing permissions
        permissions_list = []
        if self.permissions:
            try:
                permissions_list = json.loads(self.permissions)
            except (json.JSONDecodeError, TypeError):
                return
        
        # Remove permission if present
        if permission in permissions_list:
            permissions_list.remove(permission)
            self.permissions = json.dumps(permissions_list)
    
    def get_permissions_list(self) -> List[str]:
        """Get list of permissions for this role.
        
        Returns:
            List of permission strings.
        """
        if not self.permissions:
            return []
        
        import json
        try:
            return json.loads(self.permissions)
        except (json.JSONDecodeError, TypeError):
            return []
    
    def __repr__(self) -> str:
        """String representation of the role.
        
        Returns:
            String representation of the role.
        """
        return f"<Role(id={self.id}, name='{self.name}', display_name='{self.display_name}')>"
