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
        Currently only supports "memory" type. Neo4j implementation
        can be added as needed.
    """
    if cfg.kind == "neo4j":
        # TODO: Implement Neo4j graph store
        raise NotImplementedError("Neo4j graph store not yet implemented")
    elif cfg.kind == "memory":
        from graph.in_memory_graph import InMemoryGraphStore
        return InMemoryGraphStore()
    else:
        raise ValueError(f"Unsupported graph store type: {cfg.kind}")


def create_memory_graph_store() -> GraphStore:
    """Create an in-memory graph store for testing.
    
    Returns:
        In-memory graph store instance.
    """
    cfg = GraphStoreConfig("memory")
    return make_graph_store(cfg)
