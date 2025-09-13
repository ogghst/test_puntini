"""Pytest configuration and shared fixtures for the test suite.

This module provides common fixtures and configuration for testing
the puntini agent system components.
"""

import pytest
from typing import Dict, Any, List
from uuid import UUID

from puntini.graph.in_memory_graph import InMemoryGraphStore
from puntini.models.specs import NodeSpec, EdgeSpec, MatchSpec
from puntini.models.node import Node
from puntini.models.edge import Edge


@pytest.fixture
def graph_store() -> InMemoryGraphStore:
    """Create a fresh InMemoryGraphStore instance for each test.
    
    Returns:
        A new InMemoryGraphStore instance.
    """
    return InMemoryGraphStore()


@pytest.fixture
def sample_node_specs() -> List[NodeSpec]:
    """Create sample node specifications for testing.
    
    Returns:
        List of NodeSpec instances for testing.
    """
    return [
        NodeSpec(
            label="Person",
            key="john_doe",
            properties={"name": "John Doe", "age": 30, "city": "New York"}
        ),
        NodeSpec(
            label="Person",
            key="jane_smith",
            properties={"name": "Jane Smith", "age": 25, "city": "Boston"}
        ),
        NodeSpec(
            label="Company",
            key="acme_corp",
            properties={"name": "Acme Corp", "industry": "Technology", "employees": 1000}
        ),
        NodeSpec(
            label="Project",
            key="project_alpha",
            properties={"name": "Project Alpha", "status": "active", "budget": 50000}
        )
    ]


@pytest.fixture
def sample_edge_specs() -> List[EdgeSpec]:
    """Create sample edge specifications for testing.
    
    Returns:
        List of EdgeSpec instances for testing.
    """
    return [
        EdgeSpec(
            relationship_type="KNOWS",
            source_key="john_doe",
            target_key="jane_smith",
            source_label="Person",
            target_label="Person",
            properties={"since": "2020", "strength": "strong"}
        ),
        EdgeSpec(
            relationship_type="WORKS_FOR",
            source_key="john_doe",
            target_key="acme_corp",
            source_label="Person",
            target_label="Company",
            properties={"position": "Engineer", "start_date": "2021-01-01"}
        ),
        EdgeSpec(
            relationship_type="MANAGES",
            source_key="jane_smith",
            target_key="project_alpha",
            source_label="Person",
            target_label="Project",
            properties={"role": "Project Manager", "since": "2022-01-01"}
        )
    ]


@pytest.fixture
def populated_graph_store(graph_store: InMemoryGraphStore, sample_node_specs: List[NodeSpec], sample_edge_specs: List[EdgeSpec]) -> InMemoryGraphStore:
    """Create a graph store populated with sample data.
    
    Args:
        graph_store: Fresh InMemoryGraphStore instance.
        sample_node_specs: Sample node specifications.
        sample_edge_specs: Sample edge specifications.
        
    Returns:
        Graph store populated with sample nodes and edges.
    """
    # Add nodes
    for node_spec in sample_node_specs:
        graph_store.upsert_node(node_spec)
    
    # Add edges
    for edge_spec in sample_edge_specs:
        graph_store.upsert_edge(edge_spec)
    
    return graph_store


@pytest.fixture
def sample_match_specs() -> List[MatchSpec]:
    """Create sample match specifications for testing.
    
    Returns:
        List of MatchSpec instances for testing.
    """
    return [
        MatchSpec(label="Person"),
        MatchSpec(key="john_doe"),
        MatchSpec(properties={"age": 30}),
        MatchSpec(label="Person", key="jane_smith"),
        MatchSpec(properties={"city": "Boston"}),
        MatchSpec(label="Company", properties={"industry": "Technology"})
    ]


@pytest.fixture
def invalid_node_specs() -> List[NodeSpec]:
    """Create invalid node specifications for testing error handling.
    
    Returns:
        List of invalid NodeSpec instances for testing.
    """
    return [
        NodeSpec(label="", key="empty_label"),  # Empty label
        NodeSpec(label="Person", key=""),  # Empty key
        NodeSpec(label="Person", key="valid_key", properties={"invalid": None})  # Invalid property value
    ]


@pytest.fixture
def invalid_edge_specs() -> List[EdgeSpec]:
    """Create invalid edge specifications for testing error handling.
    
    Returns:
        List of invalid EdgeSpec instances for testing.
    """
    return [
        EdgeSpec(
            relationship_type="",
            source_key="john_doe",
            target_key="jane_smith",
            source_label="Person",
            target_label="Person"
        ),  # Empty relationship type
        EdgeSpec(
            relationship_type="KNOWS",
            source_key="",
            target_key="jane_smith",
            source_label="Person",
            target_label="Person"
        ),  # Empty source key
        EdgeSpec(
            relationship_type="KNOWS",
            source_key="john_doe",
            target_key="",
            source_label="Person",
            target_label="Person"
        )  # Empty target key
    ]


@pytest.fixture
def complex_graph_data() -> Dict[str, Any]:
    """Create complex graph data for integration testing.
    
    Returns:
        Dictionary containing complex graph structure for testing.
    """
    return {
        "nodes": [
            {"label": "Person", "key": "alice", "properties": {"name": "Alice", "age": 28}},
            {"label": "Person", "key": "bob", "properties": {"name": "Bob", "age": 32}},
            {"label": "Person", "key": "charlie", "properties": {"name": "Charlie", "age": 35}},
            {"label": "Company", "key": "tech_corp", "properties": {"name": "Tech Corp", "size": "large"}},
            {"label": "Project", "key": "project_beta", "properties": {"name": "Project Beta", "status": "planning"}},
            {"label": "Skill", "key": "python", "properties": {"name": "Python", "level": "expert"}},
            {"label": "Skill", "key": "javascript", "properties": {"name": "JavaScript", "level": "intermediate"}}
        ],
        "edges": [
            {"type": "KNOWS", "source": "alice", "target": "bob", "source_label": "Person", "target_label": "Person"},
            {"type": "KNOWS", "source": "bob", "target": "charlie", "source_label": "Person", "target_label": "Person"},
            {"type": "KNOWS", "source": "alice", "target": "charlie", "source_label": "Person", "target_label": "Person"},
            {"type": "WORKS_FOR", "source": "alice", "target": "tech_corp", "source_label": "Person", "target_label": "Company"},
            {"type": "WORKS_FOR", "source": "bob", "target": "tech_corp", "source_label": "Person", "target_label": "Company"},
            {"type": "MANAGES", "source": "alice", "target": "project_beta", "source_label": "Person", "target_label": "Project"},
            {"type": "HAS_SKILL", "source": "alice", "target": "python", "source_label": "Person", "target_label": "Skill"},
            {"type": "HAS_SKILL", "source": "bob", "target": "javascript", "source_label": "Person", "target_label": "Skill"},
            {"type": "HAS_SKILL", "source": "charlie", "target": "python", "source_label": "Person", "target_label": "Skill"}
        ]
    }


@pytest.fixture
def complex_populated_graph(graph_store: InMemoryGraphStore, complex_graph_data: Dict[str, Any]) -> InMemoryGraphStore:
    """Create a graph store populated with complex data for integration testing.
    
    Args:
        graph_store: Fresh InMemoryGraphStore instance.
        complex_graph_data: Complex graph data structure.
        
    Returns:
        Graph store populated with complex data.
    """
    # Add nodes
    for node_data in complex_graph_data["nodes"]:
        node_spec = NodeSpec(
            label=node_data["label"],
            key=node_data["key"],
            properties=node_data["properties"]
        )
        graph_store.upsert_node(node_spec)
    
    # Add edges
    for edge_data in complex_graph_data["edges"]:
        edge_spec = EdgeSpec(
            relationship_type=edge_data["type"],
            source_key=edge_data["source"],
            target_key=edge_data["target"],
            source_label=edge_data["source_label"],
            target_label=edge_data["target_label"]
        )
        graph_store.upsert_edge(edge_spec)
    
    return graph_store
