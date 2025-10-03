"""Parametrized tests for edge cases and boundary conditions.

This module contains parametrized tests that cover various edge cases,
boundary conditions, and error scenarios using pytest.mark.parametrize.
"""

import pytest
from typing import List, Dict, Any, Tuple

from puntini.graph.in_memory_graph import InMemoryGraphStore
from puntini.models.specs import NodeSpec, EdgeSpec, MatchSpec
from puntini.models.errors import ValidationError, NotFoundError


class TestParametrizedNodeOperations:
    """Parametrized tests for node operations."""
    
    @pytest.mark.parametrize("label,key,properties,should_raise,error_type", [
        # Valid cases
        ("Person", "john", {"age": 30}, False, None),
        ("Company", "acme", {"name": "Acme Corp"}, False, None),
        ("Project", "proj1", {}, False, None),
        ("", "valid_key", {}, True, ValidationError),  # Empty label
        ("ValidLabel", "", {}, True, ValidationError),  # Empty key
        ("ValidLabel", "valid_key", {"valid": "value"}, False, None),
    ])
    def test_upsert_node_validation(self, graph_store: InMemoryGraphStore, label: str, key: str, properties: Dict[str, Any], should_raise: bool, error_type):
        """Test node validation with various inputs."""
        node_spec = NodeSpec(label=label, key=key, properties=properties)
        
        if should_raise:
            with pytest.raises(error_type):
                graph_store.upsert_node(node_spec)
        else:
            node = graph_store.upsert_node(node_spec)
            assert node.label == label
            assert node.key == key
            assert node.properties == properties
    
    @pytest.mark.parametrize("properties_updates,expected_properties", [
        ({}, {"name": "John", "age": 30}),  # No updates
        ({"age": 31}, {"name": "John", "age": 31}),  # Single update
        ({"age": 31, "city": "NYC"}, {"name": "John", "age": 31, "city": "NYC"}),  # Multiple updates
        ({"age": 31, "name": "Johnny"}, {"name": "Johnny", "age": 31}),  # Override existing
    ])
    def test_node_property_updates(self, graph_store: InMemoryGraphStore, properties_updates: Dict[str, Any], expected_properties: Dict[str, Any]):
        """Test various property update scenarios."""
        # Create initial node
        initial_spec = NodeSpec(label="Person", key="john", properties={"name": "John", "age": 30})
        graph_store.upsert_node(initial_spec)
        
        # Update properties
        graph_store.update_props(MatchSpec(label="Person", key="john"), properties_updates)
        
        # Verify final properties
        for node in graph_store._nodes.values():
            if node.key == "john":
                assert node.properties == expected_properties
                break
        else:
            pytest.fail("Node not found")


class TestParametrizedEdgeOperations:
    """Parametrized tests for edge operations."""
    
    @pytest.mark.parametrize("rel_type,source_key,target_key,source_label,target_label,should_raise,error_type", [
        # Valid cases
        ("KNOWS", "john_doe", "jane_smith", "Person", "Person", False, None),
        ("WORKS_FOR", "john_doe", "acme_corp", "Person", "Company", False, None),
        ("", "john_doe", "jane_smith", "Person", "Person", True, ValidationError),  # Empty relationship type
        ("KNOWS", "", "jane_smith", "Person", "Person", True, ValidationError),  # Empty source key
        ("KNOWS", "john_doe", "", "Person", "Person", True, ValidationError),  # Empty target key
    ])
    def test_upsert_edge_validation(self, populated_graph_store: InMemoryGraphStore, rel_type: str, source_key: str, target_key: str, source_label: str, target_label: str, should_raise: bool, error_type):
        """Test edge validation with various inputs."""
        edge_spec = EdgeSpec(
            relationship_type=rel_type,
            source_key=source_key,
            target_key=target_key,
            source_label=source_label,
            target_label=target_label,
            properties={}
        )
        
        if should_raise:
            with pytest.raises(error_type):
                populated_graph_store.upsert_edge(edge_spec)
        else:
            edge = populated_graph_store.upsert_edge(edge_spec)
            assert edge.relationship_type == rel_type
            assert edge.source_key == source_key
            assert edge.target_key == target_key


class TestParametrizedMatchingOperations:
    """Parametrized tests for matching operations."""
    
    @pytest.mark.parametrize("match_spec,expected_matches", [
        (MatchSpec(label="Person"), 2),  # Match by label
        (MatchSpec(key="john_doe"), 1),  # Match by key
        (MatchSpec(properties={"age": 30}), 1),  # Match by property
        (MatchSpec(label="Person", key="jane_smith"), 1),  # Match by label and key
        (MatchSpec(label="Person", properties={"city": "Boston"}), 1),  # Match by label and property
        (MatchSpec(label="Nonexistent"), 0),  # No matches
        (MatchSpec(properties={"nonexistent": "value"}), 0),  # No matches
    ])
    def test_node_matching_scenarios(self, populated_graph_store: InMemoryGraphStore, match_spec: MatchSpec, expected_matches: int):
        """Test various node matching scenarios."""
        matches = []
        for node in populated_graph_store._nodes.values():
            if populated_graph_store._matches_node(node, match_spec):
                matches.append(node)
        
        assert len(matches) == expected_matches
    
    @pytest.mark.parametrize("match_spec,expected_matches", [
        (MatchSpec(label="KNOWS"), 1),  # Match by relationship type
        (MatchSpec(key="john_doe"), 2),  # Match by source or target key
        (MatchSpec(properties={"since": "2020"}), 1),  # Match by property
        (MatchSpec(label="WORKS_FOR"), 1),  # Match by different relationship type
        (MatchSpec(label="Nonexistent"), 0),  # No matches
        (MatchSpec(properties={"nonexistent": "value"}), 0),  # No matches
    ])
    def test_edge_matching_scenarios(self, populated_graph_store: InMemoryGraphStore, match_spec: MatchSpec, expected_matches: int):
        """Test various edge matching scenarios."""
        matches = []
        for edge in populated_graph_store._edges.values():
            if populated_graph_store._matches_edge(edge, match_spec):
                matches.append(edge)
        
        assert len(matches) == expected_matches


class TestParametrizedSubgraphOperations:
    """Parametrized tests for subgraph operations."""
    
    @pytest.mark.parametrize("depth,expected_nodes", [
        (0, 1),  # Only central node
        (1, 6),  # Central node + 5 direct connections
        (2, 7),  # Includes nodes reachable in 2 steps
        (3, 7),  # Max depth reached
    ])
    def test_subgraph_depth_variations(self, complex_populated_graph: InMemoryGraphStore, depth: int, expected_nodes: int):
        """Test subgraph retrieval with various depths."""
        match_spec = MatchSpec(label="Person", key="alice")
        subgraph = complex_populated_graph.get_subgraph(match_spec, depth=depth)
        
        assert len(subgraph["nodes"]) == expected_nodes
        assert subgraph["depth"] == depth
    
    @pytest.mark.parametrize("match_spec,should_raise,error_type", [
        (MatchSpec(label="Person", key="alice"), False, None),  # Valid match
        (MatchSpec(label="Person", key="bob"), False, None),  # Valid match
        (MatchSpec(label="Nonexistent"), True, NotFoundError),  # No matches
        (MatchSpec(key="nonexistent"), True, NotFoundError),  # No matches
    ])
    def test_subgraph_matching_scenarios(self, complex_populated_graph: InMemoryGraphStore, match_spec: MatchSpec, should_raise: bool, error_type):
        """Test subgraph retrieval with various matching scenarios."""
        if should_raise:
            with pytest.raises(error_type):
                complex_populated_graph.get_subgraph(match_spec)
        else:
            subgraph = complex_populated_graph.get_subgraph(match_spec)
            assert isinstance(subgraph, dict)
            assert "nodes" in subgraph
            assert "edges" in subgraph
            assert len(subgraph["nodes"]) > 0


class TestParametrizedCypherOperations:
    """Parametrized tests for Cypher query operations."""
    
    @pytest.mark.parametrize("query,expected_type,expected_min_results", [
        ("MATCH (n:Person) RETURN n", "list", 1),
        ("MATCH (n:Company) RETURN n", "list", 1),
        ("RETURN *", "list", 1),
        ("UNSUPPORTED QUERY", "list", 0),
    ])
    def test_cypher_query_variations(self, populated_graph_store: InMemoryGraphStore, query: str, expected_type: str, expected_min_results: int):
        """Test various Cypher query patterns."""
        results = populated_graph_store.run_cypher(query)
        
        assert isinstance(results, eval(expected_type))
        assert len(results) >= expected_min_results
    
    @pytest.mark.parametrize("params,should_raise", [
        (None, False),  # No parameters
        ({}, False),  # Empty parameters
        ({"key": "value"}, False),  # Valid parameters
        ({"key": None}, False),  # None value in parameters
    ])
    def test_cypher_query_parameters(self, populated_graph_store: InMemoryGraphStore, params: Dict[str, Any], should_raise: bool):
        """Test Cypher queries with various parameter types."""
        if should_raise:
            with pytest.raises(Exception):
                populated_graph_store.run_cypher("MATCH (n) RETURN n", params)
        else:
            results = populated_graph_store.run_cypher("MATCH (n) RETURN n", params)
            assert isinstance(results, list)


class TestParametrizedErrorScenarios:
    """Parametrized tests for error scenarios."""
    
    @pytest.mark.parametrize("operation,args,expected_error", [
        ("upsert_node", (NodeSpec(label="", key="test"),), ValidationError),
        ("upsert_node", (NodeSpec(label="test", key=""),), ValidationError),
        ("upsert_edge", (EdgeSpec(relationship_type="", source_key="a", target_key="b", source_label="A", target_label="B"),), ValidationError),
        ("upsert_edge", (EdgeSpec(relationship_type="REL", source_key="", target_key="b", source_label="A", target_label="B"),), ValidationError),
        ("upsert_edge", (EdgeSpec(relationship_type="REL", source_key="a", target_key="", source_label="A", target_label="B"),), ValidationError),
        ("delete_node", (MatchSpec(label="Nonexistent"),), NotFoundError),
        ("delete_edge", (MatchSpec(label="Nonexistent"),), NotFoundError),
        ("update_props", (MatchSpec(label="Nonexistent"), {"test": "value"}), NotFoundError),
        ("get_subgraph", (MatchSpec(label="Nonexistent"),), NotFoundError),
    ])
    def test_error_scenarios(self, graph_store: InMemoryGraphStore, operation: str, args: Tuple, expected_error):
        """Test various error scenarios."""
        with pytest.raises(expected_error):
            getattr(graph_store, operation)(*args)


class TestParametrizedDataTypes:
    """Parametrized tests for various data types in properties."""
    
    @pytest.mark.parametrize("properties", [
        {"string": "test"},
        {"integer": 42},
        {"float": 3.14},
        {"boolean": True},
        {"boolean_false": False},
        {"list": [1, 2, 3]},
        {"dict": {"nested": "value"}},
        {"none": None},
        {"mixed": {"str": "test", "int": 42, "bool": True, "list": [1, 2, 3]}},
    ])
    def test_node_property_data_types(self, graph_store: InMemoryGraphStore, properties: Dict[str, Any]):
        """Test node properties with various data types."""
        node_spec = NodeSpec(label="Test", key="test", properties=properties)
        node = graph_store.upsert_node(node_spec)
        
        assert node.properties == properties
    
    @pytest.mark.parametrize("properties", [
        {"string": "test"},
        {"integer": 42},
        {"float": 3.14},
        {"boolean": True},
        {"list": [1, 2, 3]},
        {"dict": {"nested": "value"}},
    ])
    def test_edge_property_data_types(self, populated_graph_store: InMemoryGraphStore, properties: Dict[str, Any]):
        """Test edge properties with various data types."""
        edge_spec = EdgeSpec(
            relationship_type="TEST",
            source_key="john_doe",
            target_key="jane_smith",
            source_label="Person",
            target_label="Person",
            properties=properties
        )
        edge = populated_graph_store.upsert_edge(edge_spec)
        
        assert edge.properties == properties


class TestParametrizedBoundaryConditions:
    """Parametrized tests for boundary conditions."""
    
    @pytest.mark.parametrize("depth", [-1, 0, 1, 2, 10, 100])
    def test_subgraph_depth_boundaries(self, complex_populated_graph: InMemoryGraphStore, depth: int):
        """Test subgraph retrieval with various depth values."""
        match_spec = MatchSpec(label="Person", key="alice")
        
        if depth < 0:
            with pytest.raises(ValidationError):
                complex_populated_graph.get_subgraph(match_spec, depth=depth)
        else:
            subgraph = complex_populated_graph.get_subgraph(match_spec, depth=depth)
            assert subgraph["depth"] == depth
            assert len(subgraph["nodes"]) >= 1  # At least the central node
    
    @pytest.mark.parametrize("count", [0, 1, 10, 100, 1000])
    def test_large_dataset_operations(self, graph_store: InMemoryGraphStore, count: int):
        """Test operations with various dataset sizes."""
        # Create nodes
        for i in range(count):
            node_spec = NodeSpec(label="Test", key=f"node_{i}", properties={"index": i})
            graph_store.upsert_node(node_spec)
        
        assert len(graph_store._nodes) == count
        
        # Create edges (connect each node to next)
        for i in range(count - 1):
            edge_spec = EdgeSpec(relationship_type="CONNECTS", source_key=f"node_{i}", target_key=f"node_{i+1}", source_label="Test", target_label="Test", properties={})
            graph_store.upsert_edge(edge_spec)
        
        if count > 1:
            assert len(graph_store._edges) == count - 1
        
        # Test bulk operations
        if count > 0:
            graph_store.update_props(MatchSpec(label="Test"), {"bulk_updated": True})

            # Verify all nodes were updated
            for node in graph_store._nodes.values():
                assert node.properties["bulk_updated"] is True

            # Test subgraph retrieval
            subgraph = graph_store.get_subgraph(MatchSpec(key="node_0"), depth=min(2, count-1))
            assert len(subgraph["nodes"]) >= 1
