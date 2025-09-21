"""Graph store interface for idempotent graph operations.

This module defines the GraphStore protocol that provides a unified interface
for graph database operations with idempotent semantics and transactional guarantees.
"""

from typing import Any, Protocol
from uuid import UUID

from ..models.specs import EdgeSpec, MatchSpec, NodeSpec
from ..models.edge import Edge
from ..models.node import Node


class GraphStore(Protocol):
    """Protocol for graph store operations with idempotent semantics.
    
    All operations must be idempotent and support transactional writes.
    The implementation should use MERGE semantics under the hood to guarantee
    idempotence and prevent duplicate writes on retries.
    """
    
    def upsert_node(self, spec: NodeSpec) -> Node:
        """Create or update a node using a natural key and idempotent semantics.

        Args:
            spec: Node specification including label, key, and properties.

        Returns:
            The persisted Node with server-assigned fields populated.

        Raises:
            ConstraintViolationError: If uniqueness constraints are violated.
            ValidationError: If the input spec is not valid.

        Notes:
            Uses MERGE under the hood to guarantee idempotence.
        """
        ...
    
    def upsert_edge(self, spec: EdgeSpec) -> Edge:
        """Create or update an edge using natural keys and idempotent semantics.

        Args:
            spec: Edge specification including relationship type, source, target, and properties.

        Returns:
            The persisted Edge with server-assigned fields populated.

        Raises:
            ConstraintViolationError: If uniqueness constraints are violated.
            ValidationError: If the input spec is not valid.

        Notes:
            Uses MERGE under the hood to guarantee idempotence.
        """
        ...
    
    def update_props(self, target: MatchSpec, props: dict) -> None:
        """Update properties of nodes or edges matching the given specification.

        Args:
            target: Specification for matching nodes or edges to update.
            props: Dictionary of properties to update.

        Raises:
            NotFoundError: If no matching nodes or edges are found.
            ValidationError: If the properties are not valid.

        Notes:
            Updates are applied atomically within a transaction.
        """
        ...
    
    def delete_node(self, match: MatchSpec) -> None:
        """Delete nodes matching the given specification.

        Args:
            match: Specification for matching nodes to delete.

        Raises:
            NotFoundError: If no matching nodes are found.

        Notes:
            Deletion is cascaded to related edges automatically.
        """
        ...
    
    def delete_edge(self, match: MatchSpec) -> None:
        """Delete edges matching the given specification.

        Args:
            match: Specification for matching edges to delete.

        Raises:
            NotFoundError: If no matching edges are found.

        Notes:
            Edge deletion does not affect the connected nodes.
        """
        ...
    
    def run_cypher(self, query: str, params: dict | None = None) -> Any:
        """Execute a raw Cypher query against the graph database.

        Args:
            query: Cypher query string to execute.
            params: Optional parameters for the query.

        Returns:
            Query results as returned by the database.

        Raises:
            QueryError: If the query is malformed or execution fails.
            ValidationError: If parameters are not valid.

        Notes:
            This method should be used sparingly and only when the high-level
            methods are insufficient. Consider adding new methods to the protocol
            instead of using raw Cypher.
        """
        ...
    
    def get_subgraph(self, match: MatchSpec, depth: int = 1) -> dict[str, Any]:
        """Retrieve a subgraph around matching nodes.

        Args:
            match: Specification for the central nodes of the subgraph.
            depth: Maximum depth of relationships to include (default: 1).

        Returns:
            Dictionary containing nodes and edges of the subgraph.

        Raises:
            NotFoundError: If no matching nodes are found.
            ValidationError: If the depth parameter is not valid.

        Notes:
            The returned subgraph includes all nodes within the specified
            depth and all edges connecting them.
        """
        ...