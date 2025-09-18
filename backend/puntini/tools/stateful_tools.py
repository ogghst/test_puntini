"""Stateful tools that can access the agent state.

This module provides tools that can access the agent state through
the LangGraph runtime context mechanism.
"""

from typing import Any, Dict, List
from langchain_core.tools import tool
from langgraph.runtime import get_runtime
from pydantic import BaseModel, Field

from ..models.specs import NodeSpec, EdgeSpec, MatchSpec


class AddNodeInput(BaseModel):
    """Input schema for add_node tool."""
    label: str = Field(description="Label for the node")
    key: str = Field(description="Unique key for the node")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Properties of the node")


class AddEdgeInput(BaseModel):
    """Input schema for add_edge tool."""
    from_node: str = Field(description="Key of the source node")
    to_node: str = Field(description="Key of the destination node")
    relationship: str = Field(description="Type of relationship")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Properties of the edge")


class UpdatePropsInput(BaseModel):
    """Input schema for update_props tool."""
    target_type: str = Field(description="Type of target: 'node' or 'edge'")
    match_spec: Dict[str, Any] = Field(description="Specification to match the target")
    properties: Dict[str, Any] = Field(description="Properties to update")


class DeleteInput(BaseModel):
    """Input schema for delete tools."""
    target_type: str = Field(description="Type of target: 'node' or 'edge'")
    match_spec: Dict[str, Any] = Field(description="Specification to match the target")


class QueryInput(BaseModel):
    """Input schema for query tools."""
    query: str = Field(description="Query string or pattern")
    limit: int = Field(default=100, description="Maximum number of results")


def _get_graph_store_from_runtime() -> Any:
    """Get graph store from LangGraph runtime context.
    
    Returns:
        Graph store instance from runtime context.
        
    Raises:
        RuntimeError: If graph store is not available in runtime context.
    """
    try:
        runtime = get_runtime()
        if hasattr(runtime, 'context') and 'graph_store' in runtime.context:
            return runtime.context['graph_store']
        else:
            raise RuntimeError("Graph store not available in runtime context")
    except Exception as e:
        raise RuntimeError(f"Failed to get graph store from runtime: {str(e)}")


@tool("add_node", args_schema=AddNodeInput)
def add_node(
    label: str,
    key: str,
    properties: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Add a new node to the graph.
    
    Args:
        label: Label for the node (e.g., 'User', 'Project', 'Task').
        key: Unique key for the node (e.g., 'user_123', 'project_abc').
        properties: Dictionary of properties for the node.
        
    Returns:
        Dictionary with operation result and created node information.
    """
    try:
        graph_store = _get_graph_store_from_runtime()
        
        # Create node specification
        node_spec = NodeSpec(
            label=label,
            key=key,
            properties=properties or {}
        )
        
        # Add node to graph store
        node = graph_store.upsert_node(node_spec)
        
        return {
            "status": "success",
            "message": f"Successfully created {label} node with key '{key}'",
            "node": {
                "id": str(node.id),
                "label": node.label,
                "key": node.key,
                "properties": node.properties
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Failed to create node: {str(e)}",
            "node": None
        }


@tool("add_edge", args_schema=AddEdgeInput)
def add_edge(
    from_node: str,
    to_node: str,
    relationship: str,
    properties: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Add a new edge/relationship to the graph.
    
    Args:
        from_node: Key of the source node.
        to_node: Key of the destination node.
        relationship: Type of relationship (e.g., 'DEPENDS_ON', 'BELONGS_TO').
        properties: Dictionary of properties for the edge.
        
    Returns:
        Dictionary with operation result and created edge information.
    """
    try:
        graph_store = _get_graph_store_from_runtime()
        
        # Create edge specification
        edge_spec = EdgeSpec(
            from_key=from_node,
            to_key=to_node,
            relationship=relationship,
            properties=properties or {}
        )
        
        # Add edge to graph store
        edge = graph_store.upsert_edge(edge_spec)
        
        return {
            "status": "success",
            "message": f"Successfully created {relationship} edge from '{from_node}' to '{to_node}'",
            "edge": {
                "id": str(edge.id),
                "from_key": edge.from_key,
                "to_key": edge.to_key,
                "relationship": edge.relationship,
                "properties": edge.properties
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Failed to create edge: {str(e)}",
            "edge": None
        }


@tool("update_props", args_schema=UpdatePropsInput)
def update_props(
    target_type: str,
    match_spec: Dict[str, Any],
    properties: Dict[str, Any]
) -> Dict[str, Any]:
    """Update properties of a node or edge.
    
    Args:
        target_type: Type of target ('node' or 'edge').
        match_spec: Specification to match the target.
        properties: Properties to update.
        
    Returns:
        Dictionary with operation result.
    """
    try:
        graph_store = _get_graph_store_from_runtime()
        
        # Create match specification
        match = MatchSpec(**match_spec)
        
        # Update properties
        graph_store.update_props(match, properties)
        
        return {
            "status": "success",
            "message": f"Successfully updated properties for {target_type}"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Failed to update properties: {str(e)}"
        }


@tool("delete_node", args_schema=DeleteInput)
def delete_node(
    target_type: str,
    match_spec: Dict[str, Any]
) -> Dict[str, Any]:
    """Delete a node from the graph.
    
    Args:
        target_type: Must be 'node'.
        match_spec: Specification to match the node to delete.
        
    Returns:
        Dictionary with operation result.
    """
    if target_type != "node":
        return {
            "status": "error",
            "error": "target_type must be 'node' for delete_node tool"
        }
    
    try:
        graph_store = _get_graph_store_from_runtime()
        
        # Create match specification
        match = MatchSpec(**match_spec)
        
        # Delete node
        graph_store.delete_node(match)
        
        return {
            "status": "success",
            "message": "Successfully deleted node"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Failed to delete node: {str(e)}"
        }


@tool("delete_edge", args_schema=DeleteInput)
def delete_edge(
    target_type: str,
    match_spec: Dict[str, Any]
) -> Dict[str, Any]:
    """Delete an edge from the graph.
    
    Args:
        target_type: Must be 'edge'.
        match_spec: Specification to match the edge to delete.
        
    Returns:
        Dictionary with operation result.
    """
    if target_type != "edge":
        return {
            "status": "error",
            "error": "target_type must be 'edge' for delete_edge tool"
        }
    
    try:
        graph_store = _get_graph_store_from_runtime()
        
        # Create match specification
        match = MatchSpec(**match_spec)
        
        # Delete edge
        graph_store.delete_edge(match)
        
        return {
            "status": "success",
            "message": "Successfully deleted edge"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Failed to delete edge: {str(e)}"
        }


@tool("query_graph", args_schema=QueryInput)
def query_graph(
    query: str,
    limit: int = 100
) -> Dict[str, Any]:
    """Query the graph using a simple pattern.
    
    Args:
        query: Query pattern (e.g., 'MATCH (n) RETURN n LIMIT 10').
        limit: Maximum number of results to return.
        
    Returns:
        Dictionary with query results.
    """
    try:
        graph_store = _get_graph_store_from_runtime()
        
        # Execute query
        results = graph_store.run_cypher(query, {"limit": limit})
        
        return {
            "status": "success",
            "message": f"Query executed successfully, found {len(results) if isinstance(results, list) else 1} results",
            "results": results if isinstance(results, list) else [results],
            "query": query
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Query failed: {str(e)}",
            "results": [],
            "query": query
        }


@tool("cypher_query", args_schema=QueryInput)
def cypher_query(
    query: str,
    limit: int = 100
) -> Dict[str, Any]:
    """Execute a custom Cypher query on the graph.
    
    Args:
        query: Cypher query string.
        limit: Maximum number of results to return.
        
    Returns:
        Dictionary with query results and execution details.
    """
    try:
        graph_store = _get_graph_store_from_runtime()
        
        # Execute Cypher query
        results = graph_store.run_cypher(query, {"limit": limit})
        
        return {
            "status": "success",
            "message": f"Cypher query executed successfully, found {len(results) if isinstance(results, list) else 1} results",
            "results": results if isinstance(results, list) else [results],
            "query": query,
            "execution_time": 0.1  # Placeholder
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Cypher query failed: {str(e)}",
            "results": [],
            "query": query
        }


# List of all available stateful tools
STATEFUL_GRAPH_TOOLS = [
    add_node,
    add_edge,
    update_props,
    delete_node,
    delete_edge,
    query_graph,
    cypher_query,
]
