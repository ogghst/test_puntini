"""Specification models for graph operations and tools.

This module defines specification classes used for graph operations,
tool definitions, and matching criteria.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from .base import BaseEntity


class NodeSpec(BaseModel):
    """Specification for creating or updating a node.
    
    This class defines the structure for node operations including
    label, key, and properties.
    """
    
    label: str = Field(..., description="Node label/type")
    key: str = Field(..., description="Natural key for the node")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Node properties")
    
    class Config:
        """Pydantic configuration for NodeSpec."""
        frozen = True


class EdgeSpec(BaseModel):
    """Specification for creating or updating an edge.
    
    This class defines the structure for edge operations including
    relationship type, source, target, and properties.
    """
    
    relationship_type: str = Field(..., description="Type of relationship")
    source_key: str = Field(..., description="Natural key of source node")
    target_key: str = Field(..., description="Natural key of target node")
    source_label: str = Field(..., description="Label of source node")
    target_label: str = Field(..., description="Label of target node")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Edge properties")
    
    class Config:
        """Pydantic configuration for EdgeSpec."""
        frozen = True


class MatchSpec(BaseModel):
    """Specification for matching nodes or edges.
    
    This class defines criteria for finding and matching graph elements
    based on labels, keys, and properties.
    """
    
    label: Optional[str] = Field(None, description="Label to match")
    key: Optional[str] = Field(None, description="Key to match")
    properties: Optional[Dict[str, Any]] = Field(None, description="Properties to match")
    id: Optional[UUID] = Field(None, description="Specific ID to match")
    
    class Config:
        """Pydantic configuration for MatchSpec."""
        frozen = True


class ToolSpec(BaseModel):
    """Specification for a tool.
    
    This class defines the structure for tool registration including
    name, description, schema, and callable.
    """
    
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    input_schema: Dict[str, Any] = Field(..., description="Tool input schema")
    callable: Any = Field(..., description="Tool callable function")
    
    class Config:
        """Pydantic configuration for ToolSpec."""
        frozen = True


class PatchSpec(BaseModel):
    """Specification for a graph patch operation.
    
    This class defines the structure for batch graph operations
    that can be applied atomically.
    """
    
    nodes: List[NodeSpec] = Field(default_factory=list, description="Nodes to create/update")
    edges: List[EdgeSpec] = Field(default_factory=list, description="Edges to create/update")
    deletes: List[MatchSpec] = Field(default_factory=list, description="Elements to delete")
    
    class Config:
        """Pydantic configuration for PatchSpec."""
        frozen = True

