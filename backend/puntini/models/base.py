"""Base entity model with UUIDv4 and timestamp management.

This module defines the BaseEntity class that provides common fields
and behavior for all domain entities in the system.
"""

from datetime import datetime
from typing import Any, Dict
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class BaseEntity(BaseModel):
    """Base entity with UUIDv4 id and timestamp management.
    
    All domain entities inherit from this class to ensure consistent
    id generation and timestamp tracking. IDs are created in code
    (not by the LLM) and validated at the boundary.
    """
    
    id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

    class Config:
        """Pydantic configuration for BaseEntity."""
        frozen = True  # Ensure immutability post-creation
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }
    
    def model_copy(self, *, update: Dict[str, Any] | None = None, **kwargs: Any) -> "BaseEntity":
        """Create a copy of the entity with updated fields.
        
        Args:
            update: Dictionary of fields to update.
            **kwargs: Additional keyword arguments for updates.
            
        Returns:
            New instance with updated fields.
            
        Notes:
            This method should be used for updates since the model is frozen.
            The updated_at timestamp is automatically updated.
        """
        if update is None:
            update = {}
        
        # Always update the updated_at timestamp
        update["updated_at"] = datetime.utcnow()
        
        return super().model_copy(update=update, **kwargs)
    
    def __str__(self) -> str:
        """String representation of the entity."""
        return f"{self.__class__.__name__}(id={self.id})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the entity."""
        return f"{self.__class__.__name__}(id={self.id}, created_at={self.created_at})"

