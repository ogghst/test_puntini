"""Patch model for batch graph operations.

This module defines the Patch class that represents a collection
of graph operations that can be applied atomically.
"""

from typing import Any, Dict, List
from uuid import UUID

from pydantic import Field

from .base import BaseEntity
from .edge import Edge
from .node import Node


class Patch(BaseEntity):
    """Represents a batch of graph operations.
    
    A patch contains a collection of nodes and edges to create/update
    and elements to delete, which can be applied atomically to the graph.
    """
    
    nodes: List[Node] = Field(default_factory=list, description="Nodes in the patch")
    edges: List[Edge] = Field(default_factory=list, description="Edges in the patch")
    deleted_node_ids: List[UUID] = Field(default_factory=list, description="IDs of deleted nodes")
    deleted_edge_ids: List[UUID] = Field(default_factory=list, description="IDs of deleted edges")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Patch metadata")
    
    def __str__(self) -> str:
        """String representation of the patch."""
        return f"Patch(nodes={len(self.nodes)}, edges={len(self.edges)}, deleted_nodes={len(self.deleted_node_ids)}, deleted_edges={len(self.deleted_edge_ids)})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the patch."""
        return f"Patch(id={self.id}, nodes={len(self.nodes)}, edges={len(self.edges)}, created_at={self.created_at})"
    
    def add_node(self, node: Node) -> None:
        """Add a node to the patch.
        
        Args:
            node: Node to add to the patch.
        """
        self.nodes.append(node)
    
    def add_edge(self, edge: Edge) -> None:
        """Add an edge to the patch.
        
        Args:
            edge: Edge to add to the patch.
        """
        self.edges.append(edge)
    
    def delete_node(self, node_id: UUID) -> None:
        """Mark a node for deletion.
        
        Args:
            node_id: ID of the node to delete.
        """
        self.deleted_node_ids.append(node_id)
    
    def delete_edge(self, edge_id: UUID) -> None:
        """Mark an edge for deletion.
        
        Args:
            edge_id: ID of the edge to delete.
        """
        self.deleted_edge_ids.append(edge_id)
    
    def is_empty(self) -> bool:
        """Check if the patch is empty.
        
        Returns:
            True if the patch has no operations, False otherwise.
        """
        return (
            len(self.nodes) == 0 and
            len(self.edges) == 0 and
            len(self.deleted_node_ids) == 0 and
            len(self.deleted_edge_ids) == 0
        )

