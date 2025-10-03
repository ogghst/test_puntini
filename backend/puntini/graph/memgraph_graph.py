"""Memgraph implementation of GraphStore interface.

This module implements the GraphStore protocol using Memgraph as the backend
graph database. It provides idempotent operations with MERGE semantics and
transactional guarantees.
"""

import json
from typing import Any, Dict, List, Optional
from uuid import UUID

from gqlalchemy import Memgraph

from ..interfaces.graph_store import GraphStore
from ..models.edge import Edge
from ..models.node import Node
from ..models.specs import EdgeSpec, MatchSpec, NodeSpec
from ..models.errors import ValidationError, NotFoundError, QueryError, ConstraintViolationError


class MemgraphGraphStore:
    """Memgraph implementation of GraphStore for production use.
    
    This implementation uses Memgraph as the backend graph database,
    providing idempotent operations with MERGE semantics and transactional
    guarantees. It uses GQLAlchemy as the Python client library.
    """
    
    def __init__(self, host: str = "127.0.0.1", port: int = 7687, 
                 username: str = "", password: str = "", 
                 use_ssl: bool = False, **kwargs):
        """Initialize the Memgraph graph store.
        
        Args:
            host: Memgraph server host.
            port: Memgraph server port.
            username: Username for authentication (optional).
            password: Password for authentication (optional).
            use_ssl: Whether to use SSL connection.
            **kwargs: Additional connection parameters.
        """
        self._connection_params = {
            "host": host,
            "port": port,
            "username": username,
            "password": password,
            "use_ssl": use_ssl,
            **kwargs
        }
        
        # Initialize Memgraph connection
        try:
            self._db = Memgraph(**self._connection_params)
            # Test connection
            self._db.execute_and_fetch("RETURN 1")
        except Exception as e:
            raise ValidationError(f"Failed to connect to Memgraph: {str(e)}")
    
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
        if not spec.label or not spec.key:
            raise ValidationError("Node label and key are required")
        
        # Prepare properties for Cypher query
        properties = {**spec.properties}
        properties["key"] = spec.key
        properties["label"] = spec.label
        
        # Use MERGE to ensure idempotence
        query = f"""
        MERGE (n:{spec.label} {{key: $key}})
        ON CREATE SET n += $props, n.created_at = timestamp()
        ON MATCH SET n += $props, n.updated_at = timestamp()
        RETURN n
        """
        
        try:
            result = self._db.execute_and_fetch(
                query, 
                key=spec.key,
                props=properties
            )
            
            if not result:
                raise QueryError("Failed to create or update node")
            
            # Extract node data from result
            node_data = result[0]["n"]
            
            # Create Node object
            node = Node(
                id=UUID(node_data["id"]),
                label=spec.label,
                key=spec.key,
                properties=properties
            )
            
            return node
            
        except Exception as e:
            if "constraint" in str(e).lower() or "unique" in str(e).lower():
                raise ConstraintViolationError(f"Constraint violation: {str(e)}")
            elif "validation" in str(e).lower():
                raise ValidationError(f"Validation error: {str(e)}")
            else:
                raise QueryError(f"Database error: {str(e)}")
    
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
        if not spec.relationship_type or not spec.source_key or not spec.target_key:
            raise ValidationError("Edge relationship type, source key, and target key are required")
        
        # Prepare properties for Cypher query
        properties = {**spec.properties}
        properties["source_key"] = spec.source_key
        properties["target_key"] = spec.target_key
        properties["source_label"] = spec.source_label
        properties["target_label"] = spec.target_label
        
        # Use MERGE to ensure idempotence
        query = f"""
        MATCH (source:{spec.source_label} {{key: $source_key}})
        MATCH (target:{spec.target_label} {{key: $target_key}})
        MERGE (source)-[r:{spec.relationship_type}]->(target)
        ON CREATE SET r += $props, r.created_at = timestamp()
        ON MATCH SET r += $props, r.updated_at = timestamp()
        RETURN r, source, target
        """
        
        try:
            result = self._db.execute_and_fetch(
                query,
                source_key=spec.source_key,
                target_key=spec.target_key,
                props=properties
            )
            
            if not result:
                raise NotFoundError(f"Source node {spec.source_label}:{spec.source_key} or target node {spec.target_label}:{spec.target_key} not found")
            
            # Extract edge and node data from result
            edge_data = result[0]["r"]
            source_data = result[0]["source"]
            target_data = result[0]["target"]
            
            # Create Edge object
            edge = Edge(
                id=UUID(edge_data["id"]),
                relationship_type=spec.relationship_type,
                source_id=UUID(source_data["id"]),
                target_id=UUID(target_data["id"]),
                source_key=spec.source_key,
                target_key=spec.target_key,
                source_label=spec.source_label,
                target_label=spec.target_label,
                properties=properties
            )
            
            return edge
            
        except NotFoundError:
            raise
        except Exception as e:
            if "constraint" in str(e).lower() or "unique" in str(e).lower():
                raise ConstraintViolationError(f"Constraint violation: {str(e)}")
            elif "validation" in str(e).lower():
                raise ValidationError(f"Validation error: {str(e)}")
            else:
                raise QueryError(f"Database error: {str(e)}")
    
    def update_props(self, target: MatchSpec, props: Dict[str, Any]) -> None:
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
        if not props:
            return  # Nothing to update
        
        # Build WHERE clause based on match criteria
        where_conditions = []
        params = {"props": props}
        
        if target.id is not None:
            where_conditions.append("id(n) = $target_id")
            params["target_id"] = target.id
        else:
            if target.label is not None:
                where_conditions.append(f"n:{target.label}")
            if target.key is not None:
                where_conditions.append("n.key = $target_key")
                params["target_key"] = target.key
            if target.properties is not None:
                for key, value in target.properties.items():
                    param_key = f"match_{key}"
                    where_conditions.append(f"n.{key} = ${param_key}")
                    params[param_key] = value
        
        if not where_conditions:
            raise ValidationError("Match specification must include at least one criteria")
        
        where_clause = " AND ".join(where_conditions)
        
        # Update nodes
        query = f"""
        MATCH (n)
        WHERE {where_clause}
        SET n += $props, n.updated_at = timestamp()
        RETURN count(n) as updated_count
        """
        
        try:
            result = self._db.execute_and_fetch(query, **params)
            
            if not result or result[0]["updated_count"] == 0:
                raise NotFoundError(f"No matching nodes found for specification: {target}")
                
        except Exception as e:
            if "validation" in str(e).lower():
                raise ValidationError(f"Validation error: {str(e)}")
            else:
                raise QueryError(f"Database error: {str(e)}")
    
    def delete_node(self, match: MatchSpec) -> None:
        """Delete nodes matching the given specification.

        Args:
            match: Specification for matching nodes to delete.

        Raises:
            NotFoundError: If no matching nodes are found.

        Notes:
            Deletion is cascaded to related edges automatically.
        """
        # Build WHERE clause based on match criteria
        where_conditions = []
        params = {}
        
        if match.id is not None:
            where_conditions.append("id(n) = $target_id")
            params["target_id"] = match.id
        else:
            if match.label is not None:
                where_conditions.append(f"n:{match.label}")
            if match.key is not None:
                where_conditions.append("n.key = $target_key")
                params["target_key"] = match.key
            if match.properties is not None:
                for key, value in match.properties.items():
                    param_key = f"match_{key}"
                    where_conditions.append(f"n.{key} = ${param_key}")
                    params[param_key] = value
        
        if not where_conditions:
            raise ValidationError("Match specification must include at least one criteria")
        
        where_clause = " AND ".join(where_conditions)
        
        # Delete nodes (and their relationships)
        query = f"""
        MATCH (n)
        WHERE {where_clause}
        DETACH DELETE n
        RETURN count(n) as deleted_count
        """
        
        try:
            result = self._db.execute_and_fetch(query, **params)
            
            if not result or result[0]["deleted_count"] == 0:
                raise NotFoundError(f"No matching nodes found for specification: {match}")
                
        except Exception as e:
            raise QueryError(f"Database error: {str(e)}")
    
    def delete_edge(self, match: MatchSpec) -> None:
        """Delete edges matching the given specification.

        Args:
            match: Specification for matching edges to delete.

        Raises:
            NotFoundError: If no matching edges are found.

        Notes:
            Edge deletion does not affect the connected nodes.
        """
        # Build WHERE clause based on match criteria
        where_conditions = []
        params = {}
        
        if match.id is not None:
            where_conditions.append("id(r) = $target_id")
            params["target_id"] = match.id
        else:
            if match.label is not None:
                where_conditions.append(f"type(r) = $rel_type")
                params["rel_type"] = match.label
            if match.key is not None:
                where_conditions.append("(r.source_key = $target_key OR r.target_key = $target_key)")
                params["target_key"] = match.key
            if match.properties is not None:
                for key, value in match.properties.items():
                    param_key = f"match_{key}"
                    where_conditions.append(f"r.{key} = ${param_key}")
                    params[param_key] = value
        
        if not where_conditions:
            raise ValidationError("Match specification must include at least one criteria")
        
        where_clause = " AND ".join(where_conditions)
        
        # Delete edges
        query = f"""
        MATCH ()-[r]->()
        WHERE {where_clause}
        DELETE r
        RETURN count(r) as deleted_count
        """
        
        try:
            result = self._db.execute_and_fetch(query, **params)
            
            if not result or result[0]["deleted_count"] == 0:
                raise NotFoundError(f"No matching edges found for specification: {match}")
                
        except Exception as e:
            raise QueryError(f"Database error: {str(e)}")
    
    def run_cypher(self, query: str, params: Dict[str, Any] | None = None) -> Any:
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
        if params is None:
            params = {}
        
        try:
            result = self._db.execute_and_fetch(query, **params)
            return result
        except Exception as e:
            if "validation" in str(e).lower():
                raise ValidationError(f"Validation error: {str(e)}")
            else:
                raise QueryError(f"Database error: {str(e)}")
    
    def get_subgraph(self, match: MatchSpec, depth: int = 1) -> Dict[str, Any]:
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
        if depth < 0:
            raise ValidationError("Depth must be non-negative")
        
        # Build WHERE clause based on match criteria
        where_conditions = []
        params = {"depth": depth}
        
        if match.id is not None:
            where_conditions.append("id(n) = $target_id")
            params["target_id"] = match.id
        else:
            if match.label is not None:
                where_conditions.append(f"n:{match.label}")
            if match.key is not None:
                where_conditions.append("n.key = $target_key")
                params["target_key"] = match.key
            if match.properties is not None:
                for key, value in match.properties.items():
                    param_key = f"match_{key}"
                    where_conditions.append(f"n.{key} = ${param_key}")
                    params[param_key] = value
        
        if not where_conditions:
            raise ValidationError("Match specification must include at least one criteria")
        
        where_clause = " AND ".join(where_conditions)
        
        # Get subgraph with specified depth
        query = f"""
        MATCH (n)
        WHERE {where_clause}
        CALL apoc.path.subgraphNodes(n, {{maxLevel: $depth}})
        YIELD node
        WITH collect(DISTINCT node) as nodes
        UNWIND nodes as node
        MATCH (node)-[r]-(connected)
        WHERE connected in nodes
        RETURN nodes, collect(DISTINCT r) as edges
        """
        
        try:
            result = self._db.execute_and_fetch(query, **params)
            
            if not result:
                raise NotFoundError(f"No matching nodes found for specification: {match}")
            
            # Convert result to expected format
            nodes_data = result[0]["nodes"]
            edges_data = result[0]["edges"]
            
            # Format nodes
            nodes = []
            for node in nodes_data:
                nodes.append({
                    "id": str(node["id"]),
                    "label": list(node.labels)[0] if node.labels else "Unknown",
                    "key": node.get("key", ""),
                    "properties": dict(node)
                })
            
            # Format edges
            edges = []
            for edge in edges_data:
                edges.append({
                    "id": str(edge["id"]),
                    "relationship_type": edge.type,
                    "source_id": str(edge.start_node["id"]),
                    "target_id": str(edge.end_node["id"]),
                    "source_key": edge.start_node.get("key", ""),
                    "target_key": edge.end_node.get("key", ""),
                    "source_label": list(edge.start_node.labels)[0] if edge.start_node.labels else "Unknown",
                    "target_label": list(edge.end_node.labels)[0] if edge.end_node.labels else "Unknown",
                    "properties": dict(edge)
                })
            
            return {
                "nodes": nodes,
                "edges": edges,
                "depth": depth,
                "central_nodes": [str(node["id"]) for node in nodes_data if self._matches_central_criteria(node, match)]
            }
            
        except NotFoundError:
            raise
        except Exception as e:
            if "validation" in str(e).lower():
                raise ValidationError(f"Validation error: {str(e)}")
            else:
                raise QueryError(f"Database error: {str(e)}")
    
    def _matches_central_criteria(self, node_data: Dict[str, Any], match: MatchSpec) -> bool:
        """Check if a node matches the central criteria for subgraph extraction.
        
        Args:
            node_data: Node data from database.
            match: Match specification.
            
        Returns:
            True if the node matches central criteria, False otherwise.
        """
        if match.id is not None:
            return str(node_data["id"]) == str(match.id)
        
        if match.label is not None and match.label not in node_data.labels:
            return False
        
        if match.key is not None and node_data.get("key") != match.key:
            return False
        
        if match.properties is not None:
            for key, value in match.properties.items():
                if node_data.get(key) != value:
                    return False
        
        return True
    
    def close(self) -> None:
        """Close the database connection.
        
        This method should be called when the graph store is no longer needed
        to properly clean up resources.
        """
        if hasattr(self._db, 'close'):
            self._db.close()
