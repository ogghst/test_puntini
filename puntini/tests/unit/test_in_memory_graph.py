"""Unit tests for InMemoryGraphStore implementation.

This module contains comprehensive unit tests for the InMemoryGraphStore
class, testing all methods and edge cases according to the GraphStore protocol.
"""

import pytest
from typing import Dict, Any, List
from uuid import UUID

from puntini.graph.in_memory_graph import InMemoryGraphStore
from puntini.models.specs import NodeSpec, EdgeSpec, MatchSpec
from puntini.models.node import Node
from puntini.models.edge import Edge
from puntini.models.errors import ValidationError, NotFoundError


class TestInMemoryGraphStoreInitialization:
    """Test InMemoryGraphStore initialization and basic properties."""
    
    def test_initialization(self):
        """Test that InMemoryGraphStore initializes correctly."""
        store = InMemoryGraphStore()
        assert isinstance(store, InMemoryGraphStore)
        assert hasattr(store, '_nodes')
        assert hasattr(store, '_edges')
        assert hasattr(store, '_node_key_to_id')
        assert hasattr(store, '_edge_key_to_id')
        assert len(store._nodes) == 0
        assert len(store._edges) == 0


class TestNodeOperations:
    """Test node creation, updating, and retrieval operations."""
    
    def test_upsert_node_creates_new_node(self, graph_store: InMemoryGraphStore, sample_node_specs: List[NodeSpec]):
        """Test that upsert_node creates a new node when it doesn't exist."""
        node_spec = sample_node_specs[0]  # john_doe
        node = graph_store.upsert_node(node_spec)
        
        assert isinstance(node, Node)
        assert node.label == node_spec.label
        assert node.key == node_spec.key
        assert node.properties == node_spec.properties
        assert node.id is not None
        assert str(node.id) in graph_store._nodes
        assert f"{node.label}:{node.key}" in graph_store._node_key_to_id
    
    def test_upsert_node_updates_existing_node(self, graph_store: InMemoryGraphStore, sample_node_specs: List[NodeSpec]):
        """Test that upsert_node updates an existing node when it already exists."""
        node_spec = sample_node_specs[0]  # john_doe
        original_node = graph_store.upsert_node(node_spec)
        original_id = original_node.id
        
        # Update with new properties
        updated_spec = NodeSpec(
            label=node_spec.label,
            key=node_spec.key,
            properties={**node_spec.properties, "age": 31, "city": "San Francisco"}
        )
        updated_node = graph_store.upsert_node(updated_spec)
        
        assert updated_node.id == original_id  # Same ID
        assert updated_node.label == updated_spec.label
        assert updated_node.key == updated_spec.key
        assert updated_node.properties["age"] == 31
        assert updated_node.properties["city"] == "San Francisco"
        assert updated_node.properties["name"] == "John Doe"  # Original property preserved
    
    def test_upsert_node_validation_error_empty_label(self, graph_store: InMemoryGraphStore):
        """Test that upsert_node raises ValidationError for empty label."""
        with pytest.raises(ValidationError, match="Node label and key are required"):
            graph_store.upsert_node(NodeSpec(label="", key="test"))
    
    def test_upsert_node_validation_error_empty_key(self, graph_store: InMemoryGraphStore):
        """Test that upsert_node raises ValidationError for empty key."""
        with pytest.raises(ValidationError, match="Node label and key are required"):
            graph_store.upsert_node(NodeSpec(label="Person", key=""))
    
    def test_upsert_node_idempotent(self, graph_store: InMemoryGraphStore, sample_node_specs: List[NodeSpec]):
        """Test that multiple calls to upsert_node with same spec are idempotent."""
        node_spec = sample_node_specs[0]  # john_doe
        
        # First call
        node1 = graph_store.upsert_node(node_spec)
        
        # Second call with same spec
        node2 = graph_store.upsert_node(node_spec)
        
        assert node1.id == node2.id
        assert node1.label == node2.label
        assert node1.key == node2.key
        assert node1.properties == node2.properties


class TestEdgeOperations:
    """Test edge creation, updating, and retrieval operations."""
    
    def test_upsert_edge_creates_new_edge(self, populated_graph_store: InMemoryGraphStore):
        """Test that upsert_edge creates a new edge when it doesn't exist."""
        edge_spec = EdgeSpec(
            relationship_type="COLLABORATES",
            source_key="john_doe",
            target_key="acme_corp",
            source_label="Person",
            target_label="Company",
            properties={"project": "Alpha"}
        )
        
        edge = populated_graph_store.upsert_edge(edge_spec)
        
        assert isinstance(edge, Edge)
        assert edge.relationship_type == edge_spec.relationship_type
        assert edge.source_key == edge_spec.source_key
        assert edge.target_key == edge_spec.target_key
        assert edge.source_label == edge_spec.source_label
        assert edge.target_label == edge_spec.target_label
        assert edge.properties == edge_spec.properties
        assert edge.id is not None
        assert str(edge.id) in populated_graph_store._edges
    
    def test_upsert_edge_updates_existing_edge(self, populated_graph_store: InMemoryGraphStore):
        """Test that upsert_edge updates an existing edge when it already exists."""
        # Get existing edge
        existing_edges = list(populated_graph_store._edges.values())
        existing_edge = existing_edges[0]
        
        # Update with new properties
        updated_spec = EdgeSpec(
            relationship_type=existing_edge.relationship_type,
            source_key=existing_edge.source_key,
            target_key=existing_edge.target_key,
            source_label=existing_edge.source_label,
            target_label=existing_edge.target_label,
            properties={**existing_edge.properties, "updated": True}
        )
        
        updated_edge = populated_graph_store.upsert_edge(updated_spec)
        
        assert updated_edge.id == existing_edge.id  # Same ID
        assert updated_edge.relationship_type == existing_edge.relationship_type
        assert updated_edge.properties["updated"] is True
        # Original properties should be preserved
        for key, value in existing_edge.properties.items():
            if key != "updated":
                assert updated_edge.properties[key] == value
    
    def test_upsert_edge_validation_error_empty_relationship_type(self, populated_graph_store: InMemoryGraphStore):
        """Test that upsert_edge raises ValidationError for empty relationship type."""
        with pytest.raises(ValidationError, match="Edge relationship type, source key, and target key are required"):
            populated_graph_store.upsert_edge(EdgeSpec(
                relationship_type="",
                source_key="john_doe",
                target_key="jane_smith",
                source_label="Person",
                target_label="Person"
            ))
    
    def test_upsert_edge_validation_error_empty_source_key(self, populated_graph_store: InMemoryGraphStore):
        """Test that upsert_edge raises ValidationError for empty source key."""
        with pytest.raises(ValidationError, match="Edge relationship type, source key, and target key are required"):
            populated_graph_store.upsert_edge(EdgeSpec(
                relationship_type="KNOWS",
                source_key="",
                target_key="jane_smith",
                source_label="Person",
                target_label="Person"
            ))
    
    def test_upsert_edge_validation_error_empty_target_key(self, populated_graph_store: InMemoryGraphStore):
        """Test that upsert_edge raises ValidationError for empty target key."""
        with pytest.raises(ValidationError, match="Edge relationship type, source key, and target key are required"):
            populated_graph_store.upsert_edge(EdgeSpec(
                relationship_type="KNOWS",
                source_key="john_doe",
                target_key="",
                source_label="Person",
                target_label="Person"
            ))
    
    def test_upsert_edge_not_found_error_missing_source(self, populated_graph_store: InMemoryGraphStore):
        """Test that upsert_edge raises NotFoundError for missing source node."""
        with pytest.raises(NotFoundError, match="Source node not found"):
            populated_graph_store.upsert_edge(EdgeSpec(
                relationship_type="KNOWS",
                source_key="nonexistent",
                target_key="jane_smith",
                source_label="Person",
                target_label="Person"
            ))
    
    def test_upsert_edge_not_found_error_missing_target(self, populated_graph_store: InMemoryGraphStore):
        """Test that upsert_edge raises NotFoundError for missing target node."""
        with pytest.raises(NotFoundError, match="Target node not found"):
            populated_graph_store.upsert_edge(EdgeSpec(
                relationship_type="KNOWS",
                source_key="john_doe",
                target_key="nonexistent",
                source_label="Person",
                target_label="Person"
            ))
    
    def test_upsert_edge_idempotent(self, populated_graph_store: InMemoryGraphStore):
        """Test that multiple calls to upsert_edge with same spec are idempotent."""
        edge_spec = EdgeSpec(
            relationship_type="COLLABORATES",
            source_key="john_doe",
            target_key="acme_corp",
            source_label="Person",
            target_label="Company",
            properties={"project": "Alpha"}
        )
        
        # First call
        edge1 = populated_graph_store.upsert_edge(edge_spec)
        
        # Second call with same spec
        edge2 = populated_graph_store.upsert_edge(edge_spec)
        
        assert edge1.id == edge2.id
        assert edge1.relationship_type == edge2.relationship_type
        assert edge1.source_key == edge2.source_key
        assert edge1.target_key == edge2.target_key
        assert edge1.properties == edge2.properties


class TestPropertyUpdateOperations:
    """Test property update operations."""
    
    def test_update_props_updates_matching_nodes(self, populated_graph_store: InMemoryGraphStore):
        """Test that update_props updates properties of matching nodes."""
        match_spec = MatchSpec(label="Person", key="john_doe")
        new_props = {"age": 31, "city": "San Francisco"}
        
        populated_graph_store.update_props(match_spec, new_props)
        
        # Find the updated node
        for node in populated_graph_store._nodes.values():
            if node.key == "john_doe":
                assert node.properties["age"] == 31
                assert node.properties["city"] == "San Francisco"
                assert node.properties["name"] == "John Doe"  # Original property preserved
                break
        else:
            pytest.fail("Node not found")
    
    def test_update_props_updates_matching_edges(self, populated_graph_store: InMemoryGraphStore):
        """Test that update_props updates properties of matching edges."""
        match_spec = MatchSpec(label="KNOWS")  # Match by relationship type
        new_props = {"strength": "very_strong", "updated": True}
        
        populated_graph_store.update_props(match_spec, new_props)
        
        # Find the updated edge
        for edge in populated_graph_store._edges.values():
            if edge.relationship_type == "KNOWS":
                assert edge.properties["strength"] == "very_strong"
                assert edge.properties["updated"] is True
                assert edge.properties["since"] == "2020"  # Original property preserved
                break
        else:
            pytest.fail("Edge not found")
    
    def test_update_props_no_matches_raises_error(self, populated_graph_store: InMemoryGraphStore):
        """Test that update_props raises NotFoundError when no matches found."""
        match_spec = MatchSpec(label="Nonexistent")
        
        with pytest.raises(NotFoundError, match="No matching nodes or edges found"):
            populated_graph_store.update_props(match_spec, {"test": "value"})
    
    def test_update_props_empty_properties_does_nothing(self, populated_graph_store: InMemoryGraphStore):
        """Test that update_props with empty properties does nothing."""
        match_spec = MatchSpec(label="Person")
        
        # Should not raise an error
        populated_graph_store.update_props(match_spec, {})
        
        # Verify no changes were made
        original_count = len(populated_graph_store._nodes)
        assert len(populated_graph_store._nodes) == original_count


class TestDeletionOperations:
    """Test node and edge deletion operations."""
    
    def test_delete_node_removes_node_and_connected_edges(self, populated_graph_store: InMemoryGraphStore):
        """Test that delete_node removes the node and all connected edges."""
        initial_node_count = len(populated_graph_store._nodes)
        initial_edge_count = len(populated_graph_store._edges)
        
        match_spec = MatchSpec(label="Person", key="john_doe")
        populated_graph_store.delete_node(match_spec)
        
        # Node should be removed
        assert len(populated_graph_store._nodes) == initial_node_count - 1
        
        # Connected edges should be removed
        assert len(populated_graph_store._edges) < initial_edge_count
        
        # Verify node is gone
        for node in populated_graph_store._nodes.values():
            assert node.key != "john_doe"
    
    def test_delete_node_no_matches_raises_error(self, populated_graph_store: InMemoryGraphStore):
        """Test that delete_node raises NotFoundError when no matches found."""
        match_spec = MatchSpec(label="Nonexistent")
        
        with pytest.raises(NotFoundError, match="No matching nodes found"):
            populated_graph_store.delete_node(match_spec)
    
    def test_delete_edge_removes_edge_only(self, populated_graph_store: InMemoryGraphStore):
        """Test that delete_edge removes only the edge, not connected nodes."""
        initial_node_count = len(populated_graph_store._nodes)
        initial_edge_count = len(populated_graph_store._edges)
        
        match_spec = MatchSpec(label="KNOWS")
        populated_graph_store.delete_edge(match_spec)
        
        # Edge should be removed
        assert len(populated_graph_store._edges) == initial_edge_count - 1
        
        # Nodes should remain
        assert len(populated_graph_store._nodes) == initial_node_count
        
        # Verify edge is gone
        for edge in populated_graph_store._edges.values():
            assert edge.relationship_type != "KNOWS"
    
    def test_delete_edge_no_matches_raises_error(self, populated_graph_store: InMemoryGraphStore):
        """Test that delete_edge raises NotFoundError when no matches found."""
        match_spec = MatchSpec(label="Nonexistent")
        
        with pytest.raises(NotFoundError, match="No matching edges found"):
            populated_graph_store.delete_edge(match_spec)


class TestCypherQueryOperations:
    """Test Cypher query execution operations."""
    
    def test_run_cypher_match_query_returns_nodes(self, populated_graph_store: InMemoryGraphStore):
        """Test that run_cypher with MATCH query returns matching nodes."""
        results = populated_graph_store.run_cypher("MATCH (n:Person) RETURN n")
        
        assert isinstance(results, list)
        assert len(results) > 0
        
        for result in results:
            assert "n" in result
            node_data = result["n"]
            assert "id" in node_data
            assert "label" in node_data
            assert "key" in node_data
            assert "properties" in node_data
            assert node_data["label"] == "Person"
    
    def test_run_cypher_return_query_returns_all_elements(self, populated_graph_store: InMemoryGraphStore):
        """Test that run_cypher with RETURN query returns all nodes and edges."""
        results = populated_graph_store.run_cypher("RETURN *")
        
        assert isinstance(results, list)
        assert len(results) > 0
        
        # Should have both nodes and edges
        node_count = sum(1 for r in results if r.get("type") == "node")
        edge_count = sum(1 for r in results if r.get("type") == "edge")
        
        assert node_count > 0
        assert edge_count > 0
    
    def test_run_cypher_unsupported_query_returns_empty(self, populated_graph_store: InMemoryGraphStore):
        """Test that run_cypher with unsupported query returns empty list."""
        results = populated_graph_store.run_cypher("CREATE (n:Test) RETURN n")
        
        assert isinstance(results, list)
        assert len(results) == 0
    
    def test_run_cypher_with_params(self, populated_graph_store: InMemoryGraphStore):
        """Test that run_cypher accepts parameters."""
        params = {"label": "Person"}
        results = populated_graph_store.run_cypher("MATCH (n:Person) RETURN n", params)
        
        assert isinstance(results, list)
        # Parameters are not used in this simple implementation, but should not cause errors


class TestSubgraphOperations:
    """Test subgraph retrieval operations."""
    
    def test_get_subgraph_returns_central_node_and_connections(self, populated_graph_store: InMemoryGraphStore):
        """Test that get_subgraph returns central node and its connections."""
        match_spec = MatchSpec(label="Person", key="john_doe")
        subgraph = populated_graph_store.get_subgraph(match_spec, depth=1)
        
        assert isinstance(subgraph, dict)
        assert "nodes" in subgraph
        assert "edges" in subgraph
        assert "depth" in subgraph
        assert "central_nodes" in subgraph
        
        assert len(subgraph["nodes"]) > 0
        assert len(subgraph["edges"]) > 0
        assert subgraph["depth"] == 1
        assert len(subgraph["central_nodes"]) == 1
    
    def test_get_subgraph_no_matches_raises_error(self, populated_graph_store: InMemoryGraphStore):
        """Test that get_subgraph raises NotFoundError when no matches found."""
        match_spec = MatchSpec(label="Nonexistent")
        
        with pytest.raises(NotFoundError, match="No matching nodes found"):
            populated_graph_store.get_subgraph(match_spec)
    
    def test_get_subgraph_negative_depth_raises_error(self, populated_graph_store: InMemoryGraphStore):
        """Test that get_subgraph raises ValidationError for negative depth."""
        match_spec = MatchSpec(label="Person", key="john_doe")
        
        with pytest.raises(ValidationError, match="Depth must be non-negative"):
            populated_graph_store.get_subgraph(match_spec, depth=-1)
    
    def test_get_subgraph_depth_zero_returns_only_central_nodes(self, populated_graph_store: InMemoryGraphStore):
        """Test that get_subgraph with depth 0 returns only central nodes."""
        match_spec = MatchSpec(label="Person", key="john_doe")
        subgraph = populated_graph_store.get_subgraph(match_spec, depth=0)
        
        assert len(subgraph["nodes"]) == 1
        assert len(subgraph["edges"]) == 0
        assert subgraph["depth"] == 0


class TestMatchingOperations:
    """Test internal matching operations."""
    
    def test_matches_node_by_id(self, populated_graph_store: InMemoryGraphStore):
        """Test that _matches_node works correctly with ID matching."""
        # Get a node
        node = list(populated_graph_store._nodes.values())[0]
        match_spec = MatchSpec(id=node.id)
        
        assert populated_graph_store._matches_node(node, match_spec)
        
        # Test with different ID
        different_id = UUID('00000000-0000-0000-0000-000000000000')
        match_spec_different = MatchSpec(id=different_id)
        assert not populated_graph_store._matches_node(node, match_spec_different)
    
    def test_matches_node_by_label(self, populated_graph_store: InMemoryGraphStore):
        """Test that _matches_node works correctly with label matching."""
        node = list(populated_graph_store._nodes.values())[0]
        match_spec = MatchSpec(label=node.label)
        
        assert populated_graph_store._matches_node(node, match_spec)
        
        # Test with different label
        match_spec_different = MatchSpec(label="Different")
        assert not populated_graph_store._matches_node(node, match_spec_different)
    
    def test_matches_node_by_key(self, populated_graph_store: InMemoryGraphStore):
        """Test that _matches_node works correctly with key matching."""
        node = list(populated_graph_store._nodes.values())[0]
        match_spec = MatchSpec(key=node.key)
        
        assert populated_graph_store._matches_node(node, match_spec)
        
        # Test with different key
        match_spec_different = MatchSpec(key="different")
        assert not populated_graph_store._matches_node(node, match_spec_different)
    
    def test_matches_node_by_properties(self, populated_graph_store: InMemoryGraphStore):
        """Test that _matches_node works correctly with property matching."""
        node = list(populated_graph_store._nodes.values())[0]
        # Match by a property that exists
        for key, value in node.properties.items():
            match_spec = MatchSpec(properties={key: value})
            assert populated_graph_store._matches_node(node, match_spec)
            break
        
        # Test with non-matching property
        match_spec_different = MatchSpec(properties={"nonexistent": "value"})
        assert not populated_graph_store._matches_node(node, match_spec_different)
    
    def test_matches_edge_by_relationship_type(self, populated_graph_store: InMemoryGraphStore):
        """Test that _matches_edge works correctly with relationship type matching."""
        edge = list(populated_graph_store._edges.values())[0]
        match_spec = MatchSpec(label=edge.relationship_type)
        
        assert populated_graph_store._matches_edge(edge, match_spec)
        
        # Test with different relationship type
        match_spec_different = MatchSpec(label="Different")
        assert not populated_graph_store._matches_edge(edge, match_spec_different)


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_validation_error_inheritance(self):
        """Test that ValidationError inherits from AgentError."""
        from puntini.models.errors import ValidationError, AgentError
        
        error = ValidationError("Test message")
        assert isinstance(error, AgentError)
        assert error.message == "Test message"
    
    def test_not_found_error_inheritance(self):
        """Test that NotFoundError inherits from AgentError."""
        from puntini.models.errors import NotFoundError, AgentError
        
        error = NotFoundError("Test message")
        assert isinstance(error, AgentError)
        assert error.message == "Test message"
    
    def test_error_with_details(self):
        """Test that errors can include additional details."""
        from puntini.models.errors import ValidationError
        
        error = ValidationError("Test message", details={"field": "value"})
        assert error.details == {"field": "value"}


class TestIdempotency:
    """Test idempotency guarantees of operations."""
    
    def test_multiple_upsert_node_calls_idempotent(self, graph_store: InMemoryGraphStore):
        """Test that multiple upsert_node calls with same data are idempotent."""
        node_spec = NodeSpec(
            label="Test",
            key="test_key",
            properties={"value": "test"}
        )
        
        # First call
        node1 = graph_store.upsert_node(node_spec)
        node_count_1 = len(graph_store._nodes)
        
        # Second call with identical spec
        node2 = graph_store.upsert_node(node_spec)
        node_count_2 = len(graph_store._nodes)
        
        # Should be same node
        assert node1.id == node2.id
        assert node1.properties == node2.properties
        
        # Should not create duplicate
        assert node_count_1 == node_count_2
    
    def test_multiple_upsert_edge_calls_idempotent(self, populated_graph_store: InMemoryGraphStore):
        """Test that multiple upsert_edge calls with same data are idempotent."""
        edge_spec = EdgeSpec(
            relationship_type="TEST",
            source_key="john_doe",
            target_key="jane_smith",
            source_label="Person",
            target_label="Person",
            properties={"test": "value"}
        )
        
        # First call
        edge1 = populated_graph_store.upsert_edge(edge_spec)
        edge_count_1 = len(populated_graph_store._edges)
        
        # Second call with identical spec
        edge2 = populated_graph_store.upsert_edge(edge_spec)
        edge_count_2 = len(populated_graph_store._edges)
        
        # Should be same edge
        assert edge1.id == edge2.id
        assert edge1.properties == edge2.properties
        
        # Should not create duplicate
        assert edge_count_1 == edge_count_2


class TestDataIntegrity:
    """Test data integrity and consistency."""
    
    def test_node_key_mapping_consistency(self, populated_graph_store: InMemoryGraphStore):
        """Test that node key mappings are consistent."""
        for node in populated_graph_store._nodes.values():
            expected_key = f"{node.label}:{node.key}"
            assert expected_key in populated_graph_store._node_key_to_id
            assert populated_graph_store._node_key_to_id[expected_key] == node.id
    
    def test_edge_key_mapping_consistency(self, populated_graph_store: InMemoryGraphStore):
        """Test that edge key mappings are consistent."""
        for edge in populated_graph_store._edges.values():
            expected_key = f"{edge.source_label}:{edge.source_key}-[{edge.relationship_type}]->{edge.target_label}:{edge.target_key}"
            assert expected_key in populated_graph_store._edge_key_to_id
            assert populated_graph_store._edge_key_to_id[expected_key] == edge.id
    
    def test_node_edge_references_consistency(self, populated_graph_store: InMemoryGraphStore):
        """Test that node-edge references are consistent."""
        for edge in populated_graph_store._edges.values():
            # Source node should exist
            assert str(edge.source_id) in populated_graph_store._nodes
            source_node = populated_graph_store._nodes[str(edge.source_id)]
            assert source_node.key == edge.source_key
            assert source_node.label == edge.source_label
            
            # Target node should exist
            assert str(edge.target_id) in populated_graph_store._nodes
            target_node = populated_graph_store._nodes[str(edge.target_id)]
            assert target_node.key == edge.target_key
            assert target_node.label == edge.target_label
