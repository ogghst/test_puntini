"""Edge model for graph relationships.

This module defines the Edge class that represents graph edges
with their relationship types, source, target, and properties.
"""

from typing import Any, Dict
from uuid import UUID

from pydantic import Field

from .base import BaseEntity


class Edge(BaseEntity):
    """Represents an edge in the graph.
    
    An edge is a relationship between two nodes with a relationship
    type, source, target, and properties.
    """
    
    relationship_type: str = Field(..., description="Type of relationship")
    source_id: UUID = Field(..., description="ID of source node")
    target_id: UUID = Field(..., description="ID of target node")
    source_key: str = Field(..., description="Natural key of source node")
    target_key: str = Field(..., description="Natural key of target node")
    source_label: str = Field(..., description="Label of source node")
    target_label: str = Field(..., description="Label of target node")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Edge properties")
    
    def __str__(self) -> str:
        """String representation of the edge."""
        return f"Edge({self.source_label}:{self.source_key} -[{self.relationship_type}]-> {self.target_label}:{self.target_key})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the edge."""
        return f"Edge(relationship_type={self.relationship_type}, source_id={self.source_id}, target_id={self.target_id}, id={self.id})"
    
    def to_spec(self) -> "EdgeSpec":
        """Convert the edge to an EdgeSpec for operations.
        
        Returns:
            EdgeSpec representation of this edge.
        """
        from .specs import EdgeSpec
        return EdgeSpec(
            relationship_type=self.relationship_type,
            source_key=self.source_key,
            target_key=self.target_key,
            source_label=self.source_label,
            target_label=self.target_label,
            properties=self.properties
        )

