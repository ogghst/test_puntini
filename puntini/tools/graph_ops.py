"""Graph operations tools for the agent.

This module implements the core graph operations tools that
the agent can use to manipulate the graph database.
"""

from typing import Any, Dict, List
from uuid import UUID

from ..interfaces.graph_store import GraphStore
from ..models.edge import Edge
from ..models.node import Node
from ..models.specs import EdgeSpec, MatchSpec, NodeSpec
from ..models.errors import ValidationError, NotFoundError


class InMemoryGraphStore:
    """In-memory implementation of GraphStore for testing.
    
    This is a simple in-memory implementation that stores nodes
    and edges in Python dictionaries for testing purposes.
    """
    
    def __init__(self):
        """Initialize the in-memory graph store."""
        self._nodes: Dict[str, Node] = {}
        self._edges: Dict[str, Edge] = {}
        self._node_key_to_id: Dict[str, UUID] = {}
        self._edge_key_to_id: Dict[str, UUID] = {}
    
    def upsert_node(self, spec: NodeSpec) -> Node:
        """Create or update a node using a natural key and idempotent semantics.

        Args:
            spec: Node specification including label, key, and properties.

        Returns:
            The persisted Node with server-assigned fields populated.

        Raises:
            ValidationError: If the input spec is not valid.
        """
        if not spec.label or not spec.key:
            raise ValidationError("Node label and key are required")
        
        # Check if node already exists
        node_key = f"{spec.label}:{spec.key}"
        if node_key in self._node_key_to_id:
            node_id = self._node_key_to_id[node_key]
            existing_node = self._nodes[str(node_id)]
            # Update existing node
            updated_node = existing_node.model_copy(update={
                "properties": {**existing_node.properties, **spec.properties}
            })
            self._nodes[str(node_id)] = updated_node
            return updated_node
        
        # Create new node
        node = Node(
            label=spec.label,
            key=spec.key,
            properties=spec.properties
        )
        self._nodes[str(node.id)] = node
        self._node_key_to_id[node_key] = node.id
        return node
    
    def upsert_edge(self, spec: EdgeSpec) -> Edge:
        """Create or update an edge using natural keys and idempotent semantics.

        Args:
            spec: Edge specification including relationship type, source, target, and properties.

        Returns:
            The persisted Edge with server-assigned fields populated.

        Raises:
            ValidationError: If the input spec is not valid.
        """
        if not spec.relationship_type or not spec.source_key or not spec.target_key:
            raise ValidationError("Edge relationship type, source key, and target key are required")
        
        # Find source and target node IDs
        source_key = f"{spec.source_label}:{spec.source_key}"
        target_key = f"{spec.target_label}:{spec.target_key}"
        
        if source_key not in self._node_key_to_id:
            raise NotFoundError(f"Source node not found: {source_key}")
        if target_key not in self._node_key_to_id:
            raise NotFoundError(f"Target node not found: {target_key}")
        
        source_id = self._node_key_to_id[source_key]
        target_id = self._node_key_to_id[target_key]
        
        # Check if edge already exists
        edge_key = f"{source_key}-[{spec.relationship_type}]->{target_key}"
        if edge_key in self._edge_key_to_id:
            edge_id = self._edge_key_to_id[edge_key]
            existing_edge = self._edges[str(edge_id)]
            # Update existing edge
            updated_edge = existing_edge.model_copy(update={
                "properties": {**existing_edge.properties, **spec.properties}
            })
            self._edges[str(edge_id)] = updated_edge
            return updated_edge
        
        # Create new edge
        edge = Edge(
            relationship_type=spec.relationship_type,
            source_id=source_id,
            target_id=target_id,
            source_key=spec.source_key,
            target_key=spec.target_key,
            source_label=spec.source_label,
            target_label=spec.target_label,
            properties=spec.properties
        )
        self._edges[str(edge.id)] = edge
        self._edge_key_to_id[edge_key] = edge.id
        return edge
    
    def update_props(self, target: MatchSpec, props: Dict[str, Any]) -> None:
        """Update properties of nodes or edges matching the given specification.

        Args:
            target: Specification for matching nodes or edges to update.
            props: Dictionary of properties to update.

        Raises:
            NotFoundError: If no matching nodes or edges are found.
        """
        # TODO: Implement property updates
        raise NotImplementedError("Property updates not yet implemented")
    
    def delete_node(self, match: MatchSpec) -> None:
        """Delete nodes matching the given specification.

        Args:
            match: Specification for matching nodes to delete.

        Raises:
            NotFoundError: If no matching nodes are found.
        """
        # TODO: Implement node deletion
        raise NotImplementedError("Node deletion not yet implemented")
    
    def delete_edge(self, match: MatchSpec) -> None:
        """Delete edges matching the given specification.

        Args:
            match: Specification for matching edges to delete.

        Raises:
            NotFoundError: If no matching edges are found.
        """
        # TODO: Implement edge deletion
        raise NotImplementedError("Edge deletion not yet implemented")
    
    def run_cypher(self, query: str, params: Dict[str, Any] | None = None) -> Any:
        """Execute a raw Cypher query against the graph database.

        Args:
            query: Cypher query string to execute.
            params: Optional parameters for the query.

        Returns:
            Query results as returned by the database.

        Raises:
            ValidationError: If parameters are not valid.
        """
        # TODO: Implement Cypher query execution
        raise NotImplementedError("Cypher queries not yet implemented")
    
    def get_subgraph(self, match: MatchSpec, depth: int = 1) -> Dict[str, Any]:
        """Retrieve a subgraph around matching nodes.

        Args:
            match: Specification for the central nodes of the subgraph.
            depth: Maximum depth of relationships to include (default: 1).

        Returns:
            Dictionary containing nodes and edges of the subgraph.

        Raises:
            NotFoundError: If no matching nodes are found.
        """
        # TODO: Implement subgraph retrieval
        raise NotImplementedError("Subgraph retrieval not yet implemented")
