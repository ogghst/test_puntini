"""Node model for graph entities.

This module defines the Node class that represents graph nodes
with their labels, keys, and properties.
"""

from typing import Any, Dict
from uuid import UUID

from pydantic import Field

from .base import BaseEntity


class Node(BaseEntity):
    """Represents a node in the graph.
    
    A node is a graph entity with a label, key, and properties.
    The label defines the type of the node, the key is a natural
    identifier, and properties store additional data.
    """
    
    label: str = Field(..., description="Node label/type")
    key: str = Field(..., description="Natural key for the node")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Node properties")
    
    def __str__(self) -> str:
        """String representation of the node."""
        return f"Node(label={self.label}, key={self.key}, id={self.id})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the node."""
        return f"Node(label={self.label}, key={self.key}, id={self.id}, properties={self.properties})"
    
    def to_spec(self) -> "NodeSpec":
        """Convert the node to a NodeSpec for operations.
        
        Returns:
            NodeSpec representation of this node.
        """
        from .specs import NodeSpec
        return NodeSpec(
            label=self.label,
            key=self.key,
            properties=self.properties
        )

