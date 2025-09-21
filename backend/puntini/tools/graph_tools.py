"""Graph manipulation tools for the agent.

This module defines all the tools available to the agent for
graph manipulation operations.
"""

from typing import Any, Dict, List, TypedDict, Optional
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from langgraph.runtime import get_runtime

from ..models.specs import NodeSpec, EdgeSpec, MatchSpec
from ..models.node import Node
from ..models.edge import Edge
from ..interfaces.graph_store import GraphStore


# TypedDict definitions for tool outputs
class NodeInfo(TypedDict):
    """Information about a node."""
    id: str
    label: str
    key: str
    properties: Dict[str, Any]


class EdgeInfo(TypedDict):
    """Information about an edge."""
    id: str
    from_key: str
    to_key: str
    relationship: str
    properties: Dict[str, Any]


class GraphToolSuccessOutput(TypedDict):
    """Base success output for graph tools."""
    status: str  # "success"
    message: str


class GraphToolErrorOutput(TypedDict):
    """Base error output for graph tools."""
    status: str  # "error"
    error: str


class AddNodeOutput(TypedDict):
    """Output for add_node tool."""
    status: str
    message: str
    node: Optional[NodeInfo]


class AddEdgeOutput(TypedDict):
    """Output for add_edge tool."""
    status: str
    message: str
    edge: Optional[EdgeInfo]


class UpdatePropsOutput(TypedDict):
    """Output for update_props tool."""
    status: str
    message: str


class DeleteOutput(TypedDict):
    """Output for delete tools."""
    status: str
    message: str


class QueryOutput(TypedDict):
    """Output for query tools."""
    status: str
    message: str
    results: List[Any]
    query: str


class CypherQueryOutput(TypedDict):
    """Output for cypher_query tool."""
    status: str
    message: str
    results: List[Any]
    query: str
    execution_time: float


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


@tool("add_node", args_schema=AddNodeInput)
def add_node(
    label: str,
    key: str,
    properties: Dict[str, Any] = None
) -> AddNodeOutput:
    """Add a new node to the graph.
    
    Args:
        label: Label for the node (e.g., 'User', 'Project', 'Task').
        key: Unique key for the node (e.g., 'user_123', 'project_abc').
        properties: Dictionary of properties for the node.
        
    Returns:
        Dictionary with operation result and created node information.
    """
    try:
        # Get graph store from runtime context
        runtime = get_runtime()
        graph_store: GraphStore = runtime.context['graph_store']
        
        # Create node specification
        node_spec = NodeSpec(
            label=label,
            key=key,
            properties=properties or {}
        )
        
        # Add node to graph store
        node = graph_store.upsert_node(node_spec)
        
        return AddNodeOutput(
            status="success",
            message=f"Successfully created {label} node with key '{key}'",
            node=NodeInfo(
                id=str(node.id),
                label=node.label,
                key=node.key,
                properties=node.properties
            )
        )
    except Exception as e:
        return AddNodeOutput(
            status="error",
            error=f"Failed to create node: {str(e)}",
            node=None
        )


@tool("add_edge", args_schema=AddEdgeInput)
def add_edge(
    from_node: str,
    to_node: str,
    relationship: str,
    properties: Dict[str, Any] = None
) -> AddEdgeOutput:
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
        # Get graph store from runtime context
        runtime = get_runtime()
        graph_store: GraphStore = runtime.context['graph_store']
        
        # Look up source and target nodes to get their labels
        # We need to find nodes by their keys to get the labels
        source_node = None
        target_node = None
        
        # Get all nodes to find the source and target
        all_nodes = graph_store.get_all_nodes()
        for node in all_nodes:
            if node.key == from_node:
                source_node = node
            elif node.key == to_node:
                target_node = node
        
        if not source_node:
            return AddEdgeOutput(
                status="error",
                error=f"Source node with key '{from_node}' not found",
                edge=None
            )
        
        if not target_node:
            return AddEdgeOutput(
                status="error",
                error=f"Target node with key '{to_node}' not found",
                edge=None
            )
        
        # Create edge specification with correct field names
        edge_spec = EdgeSpec(
            relationship_type=relationship,
            source_key=from_node,
            target_key=to_node,
            source_label=source_node.label,
            target_label=target_node.label,
            properties=properties or {}
        )
        
        # Add edge to graph store
        edge = graph_store.upsert_edge(edge_spec)
        
        return AddEdgeOutput(
            status="success",
            message=f"Successfully created {relationship} edge from '{from_node}' to '{to_node}'",
            edge=EdgeInfo(
                id=str(edge.id),
                from_key=edge.source_key,
                to_key=edge.target_key,
                relationship=edge.relationship_type,
                properties=edge.properties
            )
        )
    except Exception as e:
        return AddEdgeOutput(
            status="error",
            error=f"Failed to create edge: {str(e)}",
            edge=None
        )


@tool("update_props", args_schema=UpdatePropsInput)
def update_props(
    target_type: str,
    match_spec: Dict[str, Any],
    properties: Dict[str, Any]
) -> UpdatePropsOutput:
    """Update properties of a node or edge.
    
    Args:
        target_type: Type of target ('node' or 'edge').
        match_spec: Specification to match the target.
        properties: Properties to update.
        
    Returns:
        Dictionary with operation result.
    """
    try:
        # Get graph store from runtime context
        runtime = get_runtime()
        graph_store: GraphStore = runtime.context['graph_store']
        
        # Create match specification
        match = MatchSpec(**match_spec)
        
        # Update properties
        graph_store.update_props(match, properties)
        
        return UpdatePropsOutput(
            status="success",
            message=f"Successfully updated properties for {target_type}"
        )
    except Exception as e:
        return UpdatePropsOutput(
            status="error",
            error=f"Failed to update properties: {str(e)}"
        )


@tool("delete_node", args_schema=DeleteInput)
def delete_node(
    target_type: str,
    match_spec: Dict[str, Any]
) -> DeleteOutput:
    """Delete a node from the graph.
    
    Args:
        target_type: Must be 'node'.
        match_spec: Specification to match the node to delete.
        
    Returns:
        Dictionary with operation result.
    """
    if target_type != "node":
        return DeleteOutput(
            status="error",
            error="target_type must be 'node' for delete_node tool"
        )
    
    try:
        # Get graph store from runtime context
        runtime = get_runtime()
        graph_store: GraphStore = runtime.context['graph_store']
        
        # Create match specification
        match = MatchSpec(**match_spec)
        
        # Delete node
        graph_store.delete_node(match)
        
        return DeleteOutput(
            status="success",
            message="Successfully deleted node"
        )
    except Exception as e:
        return DeleteOutput(
            status="error",
            error=f"Failed to delete node: {str(e)}"
        )


@tool("delete_edge", args_schema=DeleteInput)
def delete_edge(
    target_type: str,
    match_spec: Dict[str, Any]
) -> DeleteOutput:
    """Delete an edge from the graph.
    
    Args:
        target_type: Must be 'edge'.
        match_spec: Specification to match the edge to delete.
        
    Returns:
        Dictionary with operation result.
    """
    if target_type != "edge":
        return DeleteOutput(
            status="error",
            error="target_type must be 'edge' for delete_edge tool"
        )
    
    try:
        # Get graph store from runtime context
        runtime = get_runtime()
        graph_store: GraphStore = runtime.context['graph_store']
        
        # Create match specification
        match = MatchSpec(**match_spec)
        
        # Delete edge
        graph_store.delete_edge(match)
        
        return DeleteOutput(
            status="success",
            message="Successfully deleted edge"
        )
    except Exception as e:
        return DeleteOutput(
            status="error",
            error=f"Failed to delete edge: {str(e)}"
        )


@tool("query_graph", args_schema=QueryInput)
def query_graph(
    query: str,
    limit: int = 100
) -> QueryOutput:
    """Query the graph using a simple pattern.
    
    Args:
        query: Query pattern (e.g., 'MATCH (n) RETURN n LIMIT 10').
        limit: Maximum number of results to return.
        
    Returns:
        Dictionary with query results.
    """
    try:
        # Get graph store from runtime context
        runtime = get_runtime()
        graph_store: GraphStore = runtime.context['graph_store']
        
        # Execute query
        results = graph_store.run_cypher(query, {"limit": limit})
        
        return QueryOutput(
            status="success",
            message=f"Query executed successfully, found {len(results) if isinstance(results, list) else 1} results",
            results=results if isinstance(results, list) else [results],
            query=query
        )
    except Exception as e:
        return QueryOutput(
            status="error",
            error=f"Query failed: {str(e)}",
            results=[],
            query=query
        )


@tool("cypher_query", args_schema=QueryInput)
def cypher_query(
    query: str,
    limit: int = 100
) -> CypherQueryOutput:
    """Execute a custom Cypher query on the graph.
    
    Args:
        query: Cypher query string.
        limit: Maximum number of results to return.
        
    Returns:
        Dictionary with query results and execution details.
    """
    try:
        # Get graph store from runtime context
        runtime = get_runtime()
        graph_store: GraphStore = runtime.context['graph_store']
        
        # Execute Cypher query
        results = graph_store.run_cypher(query, {"limit": limit})
        
        return CypherQueryOutput(
            status="success",
            message=f"Cypher query executed successfully, found {len(results) if isinstance(results, list) else 1} results",
            results=results if isinstance(results, list) else [results],
            query=query,
            execution_time=0.1  # Placeholder
        )
    except Exception as e:
        return CypherQueryOutput(
            status="error",
            error=f"Cypher query failed: {str(e)}",
            results=[],
            query=query,
            execution_time=0.0
        )


# List of all available tools
GRAPH_TOOLS = [
    add_node,
    add_edge,
    update_props,
    delete_node,
    delete_edge,
    query_graph,
    cypher_query,
]
