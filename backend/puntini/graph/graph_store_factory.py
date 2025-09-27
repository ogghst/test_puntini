"""Factory for creating graph store instances.

This module provides factory functions for creating different
types of graph store implementations.
"""

from typing import Any, Dict
from ..interfaces.graph_store import GraphStore


class GraphStoreConfig:
    """Configuration for graph store instances."""
    
    def __init__(self, kind: str, **kwargs: Any):
        """Initialize graph store configuration.
        
        Args:
            kind: Type of graph store ("neo4j", "memory").
            **kwargs: Additional configuration parameters.
        """
        self.kind = kind
        self.config = kwargs


def make_graph_store(cfg: GraphStoreConfig) -> GraphStore:
    """Create a graph store instance based on configuration.
    
    Args:
        cfg: Graph store configuration.
        
    Returns:
        Configured graph store instance.
        
    Raises:
        ValueError: If the graph store type is not supported.
        
    Notes:
        Supports "memory", "memgraph", and "neo4j" types. Neo4j implementation
        is not yet implemented.
    """
    if cfg.kind == "neo4j":
        # TODO: Implement Neo4j graph store
        raise NotImplementedError("Neo4j graph store not yet implemented")
    elif cfg.kind == "memory":
        from .in_memory_graph import InMemoryGraphStore
        return InMemoryGraphStore()
    elif cfg.kind == "memgraph":
        from .memgraph_graph import MemgraphGraphStore
        return MemgraphGraphStore(**cfg.config)
    else:
        raise ValueError(f"Unsupported graph store type: {cfg.kind}")


def create_memory_graph_store() -> GraphStore:
    """Create an in-memory graph store for testing.
    
    Returns:
        In-memory graph store instance.
    """
    cfg = GraphStoreConfig("memory")
    return make_graph_store(cfg)


def create_memgraph_graph_store(host: str = "127.0.0.1", port: int = 7687,
                               username: str = "", password: str = "",
                               use_ssl: bool = False, **kwargs) -> GraphStore:
    """Create a Memgraph graph store for production use.
    
    Args:
        host: Memgraph server host.
        port: Memgraph server port.
        username: Username for authentication (optional).
        password: Password for authentication (optional).
        use_ssl: Whether to use SSL connection.
        **kwargs: Additional connection parameters.
    
    Returns:
        Memgraph graph store instance.
    """
    cfg = GraphStoreConfig(
        "memgraph",
        host=host,
        port=port,
        username=username,
        password=password,
        use_ssl=use_ssl,
        **kwargs
    )
    return make_graph_store(cfg)
