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
    Implements the GraphStore protocol with idempotent semantics.
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
        if not props:
            return  # Nothing to update
        
        updated_count = 0
        
        # Update nodes
        for node_id, node in self._nodes.items():
            if self._matches_node(node, target):
                updated_node = node.model_copy(update={
                    "properties": {**node.properties, **props}
                })
                self._nodes[node_id] = updated_node
                updated_count += 1
        
        # Update edges
        for edge_id, edge in self._edges.items():
            if self._matches_edge(edge, target):
                updated_edge = edge.model_copy(update={
                    "properties": {**edge.properties, **props}
                })
                self._edges[edge_id] = updated_edge
                updated_count += 1
        
        if updated_count == 0:
            raise NotFoundError(f"No matching nodes or edges found for specification: {target}")
    
    def delete_node(self, match: MatchSpec) -> None:
        """Delete nodes matching the given specification.

        Args:
            match: Specification for matching nodes to delete.

        Raises:
            NotFoundError: If no matching nodes are found.
        """
        nodes_to_delete = []
        
        # Find nodes to delete
        for node_id, node in self._nodes.items():
            if self._matches_node(node, match):
                nodes_to_delete.append((node_id, node))
        
        if not nodes_to_delete:
            raise NotFoundError(f"No matching nodes found for specification: {match}")
        
        # Delete nodes and their associated edges
        for node_id, node in nodes_to_delete:
            # Delete all edges connected to this node
            edges_to_delete = []
            for edge_id, edge in self._edges.items():
                if edge.source_id == node.id or edge.target_id == node.id:
                    edges_to_delete.append(edge_id)
            
            # Remove edges
            for edge_id in edges_to_delete:
                edge = self._edges[edge_id]
                edge_key = f"{edge.source_label}:{edge.source_key}-[{edge.relationship_type}]->{edge.target_label}:{edge.target_key}"
                del self._edges[edge_id]
                if edge_key in self._edge_key_to_id:
                    del self._edge_key_to_id[edge_key]
            
            # Remove node
            node_key = f"{node.label}:{node.key}"
            del self._nodes[node_id]
            if node_key in self._node_key_to_id:
                del self._node_key_to_id[node_key]
    
    def delete_edge(self, match: MatchSpec) -> None:
        """Delete edges matching the given specification.

        Args:
            match: Specification for matching edges to delete.

        Raises:
            NotFoundError: If no matching edges are found.
        """
        edges_to_delete = []
        
        # Find edges to delete
        for edge_id, edge in self._edges.items():
            if self._matches_edge(edge, match):
                edges_to_delete.append((edge_id, edge))
        
        if not edges_to_delete:
            raise NotFoundError(f"No matching edges found for specification: {match}")
        
        # Delete edges
        for edge_id, edge in edges_to_delete:
            edge_key = f"{edge.source_label}:{edge.source_key}-[{edge.relationship_type}]->{edge.target_label}:{edge.target_key}"
            del self._edges[edge_id]
            if edge_key in self._edge_key_to_id:
                del self._edge_key_to_id[edge_key]
    
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
        # For in-memory implementation, we'll provide basic query support
        # This is a simplified implementation that supports basic MATCH queries
        
        if params is None:
            params = {}
        
        # Basic query parsing and execution
        query_lower = query.lower().strip()
        
        if query_lower.startswith('match'):
            return self._execute_match_query(query, params)
        elif query_lower.startswith('return'):
            return self._execute_return_query(query, params)
        else:
            # For unsupported queries, return empty result
            return []
    
    def _execute_match_query(self, query: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute a MATCH query against the in-memory graph.
        
        Args:
            query: Cypher MATCH query.
            params: Query parameters.
            
        Returns:
            List of matching results.
        """
        results = []
        query_lower = query.lower()
        
        # Extract label from query if specified (e.g., "MATCH (n:Person)")
        label_filter = None
        if ':person' in query_lower:
            label_filter = 'Person'
        elif ':company' in query_lower:
            label_filter = 'Company'
        elif ':project' in query_lower:
            label_filter = 'Project'
        elif ':milestone' in query_lower:
            label_filter = 'Milestone'
        elif ':employee' in query_lower:
            label_filter = 'Employee'
        elif ':skill' in query_lower:
            label_filter = 'Skill'
        
        # Match nodes
        for node in self._nodes.values():
            if label_filter is None or node.label == label_filter:
                results.append({
                    'n': {
                        'id': str(node.id),
                        'label': node.label,
                        'key': node.key,
                        'properties': node.properties
                    }
                })
        
        return results
    
    def _execute_return_query(self, query: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute a RETURN query against the in-memory graph.
        
        Args:
            query: Cypher RETURN query.
            params: Query parameters.
            
        Returns:
            List of returned results.
        """
        # For basic return queries, return all nodes and edges
        results = []
        
        # Add all nodes
        for node in self._nodes.values():
            results.append({
                'type': 'node',
                'id': str(node.id),
                'label': node.label,
                'key': node.key,
                'properties': node.properties
            })
        
        # Add all edges
        for edge in self._edges.values():
            results.append({
                'type': 'edge',
                'id': str(edge.id),
                'relationship_type': edge.relationship_type,
                'source_id': str(edge.source_id),
                'target_id': str(edge.target_id),
                'properties': edge.properties
            })
        
        return results
    
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
        if depth < 0:
            raise ValidationError("Depth must be non-negative")
        
        # Find central nodes
        central_nodes = []
        for node in self._nodes.values():
            if self._matches_node(node, match):
                central_nodes.append(node)
        
        if not central_nodes:
            raise NotFoundError(f"No matching nodes found for specification: {match}")
        
        # Collect nodes and edges within depth
        subgraph_nodes = set()
        subgraph_edges = set()
        
        # Start with central nodes
        current_level = central_nodes
        subgraph_nodes.update(node.id for node in current_level)
        
        # Expand by depth
        for _ in range(depth):
            next_level = []
            
            for node in current_level:
                # Find all edges connected to this node
                for edge in self._edges.values():
                    if edge.source_id == node.id or edge.target_id == node.id:
                        if edge.id not in subgraph_edges:
                            subgraph_edges.add(edge.id)
                            
                            # Add connected nodes
                            connected_node_id = edge.target_id if edge.source_id == node.id else edge.source_id
                            if connected_node_id not in subgraph_nodes:
                                connected_node = self._nodes.get(str(connected_node_id))
                                if connected_node:
                                    next_level.append(connected_node)
                                    subgraph_nodes.add(connected_node_id)
            
            current_level = next_level
            if not current_level:
                break
        
        # Build result
        result_nodes = []
        result_edges = []
        
        for node_id in subgraph_nodes:
            node = self._nodes.get(str(node_id))
            if node:
                result_nodes.append({
                    'id': str(node.id),
                    'label': node.label,
                    'key': node.key,
                    'properties': node.properties
                })
        
        for edge_id in subgraph_edges:
            edge = self._edges.get(str(edge_id))
            if edge:
                result_edges.append({
                    'id': str(edge.id),
                    'relationship_type': edge.relationship_type,
                    'source_id': str(edge.source_id),
                    'target_id': str(edge.target_id),
                    'source_key': edge.source_key,
                    'target_key': edge.target_key,
                    'source_label': edge.source_label,
                    'target_label': edge.target_label,
                    'properties': edge.properties
                })
        
        return {
            'nodes': result_nodes,
            'edges': result_edges,
            'depth': depth,
            'central_nodes': [str(node.id) for node in central_nodes]
        }
    
    def _matches_node(self, node: Node, match: MatchSpec) -> bool:
        """Check if a node matches the given specification.
        
        Args:
            node: Node to check.
            match: Match specification.
            
        Returns:
            True if the node matches, False otherwise.
        """
        # Match by ID if specified
        if match.id is not None and node.id != match.id:
            return False
        
        # Match by label if specified
        if match.label is not None and node.label != match.label:
            return False
        
        # Match by key if specified
        if match.key is not None and node.key != match.key:
            return False
        
        # Match by properties if specified
        if match.properties is not None:
            for key, value in match.properties.items():
                if key not in node.properties or node.properties[key] != value:
                    return False
        
        return True
    
    def _matches_edge(self, edge: Edge, match: MatchSpec) -> bool:
        """Check if an edge matches the given specification.
        
        Args:
            edge: Edge to check.
            match: Match specification.
            
        Returns:
            True if the edge matches, False otherwise.
        """
        # Match by ID if specified
        if match.id is not None and edge.id != match.id:
            return False
        
        # Match by label if specified (relationship type)
        if match.label is not None and edge.relationship_type != match.label:
            return False
        
        # Match by key if specified (source or target key)
        if match.key is not None and edge.source_key != match.key and edge.target_key != match.key:
            return False
        
        # Match by properties if specified
        if match.properties is not None:
            for key, value in match.properties.items():
                if key not in edge.properties or edge.properties[key] != value:
                    return False
        
        return True
    
    def get_all_nodes(self) -> List[Node]:
        """Get all nodes in the graph.
        
        Returns:
            List of all nodes in the graph.
        """
        return list(self._nodes.values())
    
    def get_all_edges(self) -> List[Edge]:
        """Get all edges in the graph.
        
        Returns:
            List of all edges in the graph.
        """
        return list(self._edges.values())