"""Unit tests for MemgraphGraphStore implementation.

This module contains comprehensive unit tests for the MemgraphGraphStore
class, testing all methods and edge cases according to the GraphStore protocol.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List
from uuid import UUID

from puntini.graph.memgraph_graph import MemgraphGraphStore
from puntini.models.specs import NodeSpec, EdgeSpec, MatchSpec
from puntini.models.node import Node
from puntini.models.edge import Edge
from puntini.models.errors import ValidationError, NotFoundError, QueryError, ConstraintViolationError


class TestMemgraphGraphStoreInitialization:
    """Test MemgraphGraphStore initialization and basic properties."""
    
    @patch('puntini.graph.memgraph_graph.Memgraph')
    def test_initialization_with_default_params(self, mock_memgraph_class):
        """Test that MemgraphGraphStore initializes with default parameters."""
        mock_db = Mock()
        mock_db.execute_and_fetch.return_value = [{"result": 1}]
        mock_memgraph_class.return_value = mock_db
        
        store = MemgraphGraphStore()
        
        assert isinstance(store, MemgraphGraphStore)
        assert hasattr(store, '_db')
        assert hasattr(store, '_connection_params')
        assert store._connection_params["host"] == "127.0.0.1"
        assert store._connection_params["port"] == 7687
        assert store._connection_params["username"] == ""
        assert store._connection_params["password"] == ""
        assert store._connection_params["use_ssl"] is False
    
    @patch('puntini.graph.memgraph_graph.Memgraph')
    def test_initialization_with_custom_params(self, mock_memgraph_class):
        """Test that MemgraphGraphStore initializes with custom parameters."""
        mock_db = Mock()
        mock_db.execute_and_fetch.return_value = [{"result": 1}]
        mock_memgraph_class.return_value = mock_db
        
        store = MemgraphGraphStore(
            host="localhost",
            port=7474,
            username="user",
            password="pass",
            use_ssl=True
        )
        
        assert store._connection_params["host"] == "localhost"
        assert store._connection_params["port"] == 7474
        assert store._connection_params["username"] == "user"
        assert store._connection_params["password"] == "pass"
        assert store._connection_params["use_ssl"] is True
    
    @patch('puntini.graph.memgraph_graph.Memgraph')
    def test_initialization_connection_failure(self, mock_memgraph_class):
        """Test that MemgraphGraphStore raises ValidationError on connection failure."""
        mock_db = Mock()
        mock_db.execute_and_fetch.side_effect = Exception("Connection failed")
        mock_memgraph_class.return_value = mock_db
        
        with pytest.raises(ValidationError, match="Failed to connect to Memgraph"):
            MemgraphGraphStore()


class TestNodeOperations:
    """Test node creation, updating, and retrieval operations."""
    
    @pytest.fixture
    def mock_memgraph_store(self):
        """Create a MemgraphGraphStore with mocked database."""
        with patch('puntini.graph.memgraph_graph.Memgraph') as mock_memgraph_class:
            mock_db = Mock()
            mock_db.execute_and_fetch.return_value = [{"result": 1}]
            mock_memgraph_class.return_value = mock_db
            
            store = MemgraphGraphStore()
            store._db = mock_db
            return store
    
    def test_upsert_node_creates_new_node(self, mock_memgraph_store):
        """Test that upsert_node creates a new node when it doesn't exist."""
        # Mock database response
        mock_node_data = {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "label": "Person",
            "key": "john_doe",
            "name": "John Doe",
            "age": 30
        }
        mock_memgraph_store._db.execute_and_fetch.return_value = [{"n": mock_node_data}]
        
        node_spec = NodeSpec(
            label="Person",
            key="john_doe",
            properties={"name": "John Doe", "age": 30}
        )
        
        node = mock_memgraph_store.upsert_node(node_spec)
        
        assert isinstance(node, Node)
        assert node.label == node_spec.label
        assert node.key == node_spec.key
        assert node.properties["name"] == "John Doe"
        assert node.properties["age"] == 30
        assert str(node.id) == "550e8400-e29b-41d4-a716-446655440000"
    
    def test_upsert_node_updates_existing_node(self, mock_memgraph_store):
        """Test that upsert_node updates an existing node when it already exists."""
        # Mock database response
        mock_node_data = {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "label": "Person",
            "key": "john_doe",
            "name": "John Doe",
            "age": 31,
            "city": "San Francisco"
        }
        mock_memgraph_store._db.execute_and_fetch.return_value = [{"n": mock_node_data}]
        
        node_spec = NodeSpec(
            label="Person",
            key="john_doe",
            properties={"age": 31, "city": "San Francisco"}
        )
        
        node = mock_memgraph_store.upsert_node(node_spec)
        
        assert node.label == node_spec.label
        assert node.key == node_spec.key
        assert node.properties["age"] == 31
        assert node.properties["city"] == "San Francisco"
    
    def test_upsert_node_validation_error_empty_label(self, mock_memgraph_store):
        """Test that upsert_node raises ValidationError for empty label."""
        with pytest.raises(ValidationError, match="Node label and key are required"):
            mock_memgraph_store.upsert_node(NodeSpec(label="", key="test"))
    
    def test_upsert_node_validation_error_empty_key(self, mock_memgraph_store):
        """Test that upsert_node raises ValidationError for empty key."""
        with pytest.raises(ValidationError, match="Node label and key are required"):
            mock_memgraph_store.upsert_node(NodeSpec(label="Person", key=""))
    
    def test_upsert_node_database_error(self, mock_memgraph_store):
        """Test that upsert_node handles database errors correctly."""
        mock_memgraph_store._db.execute_and_fetch.side_effect = Exception("Database error")
        
        node_spec = NodeSpec(label="Person", key="test")
        
        with pytest.raises(QueryError, match="Database error"):
            mock_memgraph_store.upsert_node(node_spec)
    
    def test_upsert_node_constraint_violation(self, mock_memgraph_store):
        """Test that upsert_node raises ConstraintViolationError for constraint violations."""
        mock_memgraph_store._db.execute_and_fetch.side_effect = Exception("Constraint violation")
        
        node_spec = NodeSpec(label="Person", key="test")
        
        with pytest.raises(ConstraintViolationError, match="Constraint violation"):
            mock_memgraph_store.upsert_node(node_spec)


class TestEdgeOperations:
    """Test edge creation, updating, and retrieval operations."""
    
    @pytest.fixture
    def mock_memgraph_store(self):
        """Create a MemgraphGraphStore with mocked database."""
        with patch('puntini.graph.memgraph_graph.Memgraph') as mock_memgraph_class:
            mock_db = Mock()
            mock_db.execute_and_fetch.return_value = [{"result": 1}]
            mock_memgraph_class.return_value = mock_db
            
            store = MemgraphGraphStore()
            store._db = mock_db
            return store
    
    def test_upsert_edge_creates_new_edge(self, mock_memgraph_store):
        """Test that upsert_edge creates a new edge when it doesn't exist."""
        # Mock database response
        mock_edge_data = {
            "id": "550e8400-e29b-41d4-a716-446655440001",
            "relationship_type": "KNOWS",
            "source_key": "john_doe",
            "target_key": "jane_smith"
        }
        mock_source_data = {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "label": "Person",
            "key": "john_doe"
        }
        mock_target_data = {
            "id": "550e8400-e29b-41d4-a716-446655440002",
            "label": "Person",
            "key": "jane_smith"
        }
        
        mock_memgraph_store._db.execute_and_fetch.return_value = [{
            "r": mock_edge_data,
            "source": mock_source_data,
            "target": mock_target_data
        }]
        
        edge_spec = EdgeSpec(
            relationship_type="KNOWS",
            source_key="john_doe",
            target_key="jane_smith",
            source_label="Person",
            target_label="Person",
            properties={"since": "2020"}
        )
        
        edge = mock_memgraph_store.upsert_edge(edge_spec)
        
        assert isinstance(edge, Edge)
        assert edge.relationship_type == edge_spec.relationship_type
        assert edge.source_key == edge_spec.source_key
        assert edge.target_key == edge_spec.target_key
        assert edge.source_label == edge_spec.source_label
        assert edge.target_label == edge_spec.target_label
        assert edge.properties["since"] == "2020"
    
    def test_upsert_edge_validation_error_empty_relationship_type(self, mock_memgraph_store):
        """Test that upsert_edge raises ValidationError for empty relationship type."""
        with pytest.raises(ValidationError, match="Edge relationship type, source key, and target key are required"):
            mock_memgraph_store.upsert_edge(EdgeSpec(
                relationship_type="",
                source_key="john_doe",
                target_key="jane_smith",
                source_label="Person",
                target_label="Person"
            ))
    
    def test_upsert_edge_validation_error_empty_source_key(self, mock_memgraph_store):
        """Test that upsert_edge raises ValidationError for empty source key."""
        with pytest.raises(ValidationError, match="Edge relationship type, source key, and target key are required"):
            mock_memgraph_store.upsert_edge(EdgeSpec(
                relationship_type="KNOWS",
                source_key="",
                target_key="jane_smith",
                source_label="Person",
                target_label="Person"
            ))
    
    def test_upsert_edge_validation_error_empty_target_key(self, mock_memgraph_store):
        """Test that upsert_edge raises ValidationError for empty target key."""
        with pytest.raises(ValidationError, match="Edge relationship type, source key, and target key are required"):
            mock_memgraph_store.upsert_edge(EdgeSpec(
                relationship_type="KNOWS",
                source_key="john_doe",
                target_key="",
                source_label="Person",
                target_label="Person"
            ))
    
    def test_upsert_edge_not_found_error(self, mock_memgraph_store):
        """Test that upsert_edge raises NotFoundError when nodes don't exist."""
        mock_memgraph_store._db.execute_and_fetch.return_value = []  # Empty result
        
        edge_spec = EdgeSpec(
            relationship_type="KNOWS",
            source_key="nonexistent",
            target_key="also_nonexistent",
            source_label="Person",
            target_label="Person"
        )
        
        with pytest.raises(NotFoundError, match="Source node.*or target node.*not found"):
            mock_memgraph_store.upsert_edge(edge_spec)


class TestPropertyUpdateOperations:
    """Test property update operations."""
    
    @pytest.fixture
    def mock_memgraph_store(self):
        """Create a MemgraphGraphStore with mocked database."""
        with patch('puntini.graph.memgraph_graph.Memgraph') as mock_memgraph_class:
            mock_db = Mock()
            mock_db.execute_and_fetch.return_value = [{"result": 1}]
            mock_memgraph_class.return_value = mock_db
            
            store = MemgraphGraphStore()
            store._db = mock_db
            return store
    
    def test_update_props_updates_matching_nodes(self, mock_memgraph_store):
        """Test that update_props updates properties of matching nodes."""
        mock_memgraph_store._db.execute_and_fetch.return_value = [{"updated_count": 1}]
        
        match_spec = MatchSpec(label="Person", key="john_doe")
        new_props = {"age": 31, "city": "San Francisco"}
        
        mock_memgraph_store.update_props(match_spec, new_props)
        
        # Verify the query was called with correct parameters
        mock_memgraph_store._db.execute_and_fetch.assert_called_once()
        call_args = mock_memgraph_store._db.execute_and_fetch.call_args
        assert "props" in call_args[1]
        assert call_args[1]["props"] == new_props
    
    def test_update_props_no_matches_raises_error(self, mock_memgraph_store):
        """Test that update_props raises NotFoundError when no matches found."""
        mock_memgraph_store._db.execute_and_fetch.return_value = [{"updated_count": 0}]
        
        match_spec = MatchSpec(label="Nonexistent")
        
        with pytest.raises(NotFoundError, match="No matching nodes found"):
            mock_memgraph_store.update_props(match_spec, {"test": "value"})
    
    def test_update_props_empty_properties_does_nothing(self, mock_memgraph_store):
        """Test that update_props with empty properties does nothing."""
        match_spec = MatchSpec(label="Person")
        
        # Should not raise an error and not call the database
        mock_memgraph_store.update_props(match_spec, {})
        
        # Verify no database call was made
        mock_memgraph_store._db.execute_and_fetch.assert_not_called()
    
    def test_update_props_validation_error_empty_match_spec(self, mock_memgraph_store):
        """Test that update_props raises ValidationError for empty match specification."""
        match_spec = MatchSpec()  # No criteria specified
        
        with pytest.raises(ValidationError, match="Match specification must include at least one criteria"):
            mock_memgraph_store.update_props(match_spec, {"test": "value"})


class TestDeletionOperations:
    """Test node and edge deletion operations."""
    
    @pytest.fixture
    def mock_memgraph_store(self):
        """Create a MemgraphGraphStore with mocked database."""
        with patch('puntini.graph.memgraph_graph.Memgraph') as mock_memgraph_class:
            mock_db = Mock()
            mock_db.execute_and_fetch.return_value = [{"result": 1}]
            mock_memgraph_class.return_value = mock_db
            
            store = MemgraphGraphStore()
            store._db = mock_db
            return store
    
    def test_delete_node_removes_node_and_connected_edges(self, mock_memgraph_store):
        """Test that delete_node removes the node and all connected edges."""
        mock_memgraph_store._db.execute_and_fetch.return_value = [{"deleted_count": 1}]
        
        match_spec = MatchSpec(label="Person", key="john_doe")
        mock_memgraph_store.delete_node(match_spec)
        
        # Verify the query was called
        mock_memgraph_store._db.execute_and_fetch.assert_called_once()
        call_args = mock_memgraph_store._db.execute_and_fetch.call_args
        query = call_args[0][0]
        assert "DETACH DELETE" in query
    
    def test_delete_node_no_matches_raises_error(self, mock_memgraph_store):
        """Test that delete_node raises NotFoundError when no matches found."""
        mock_memgraph_store._db.execute_and_fetch.return_value = [{"deleted_count": 0}]
        
        match_spec = MatchSpec(label="Nonexistent")
        
        with pytest.raises(NotFoundError, match="No matching nodes found"):
            mock_memgraph_store.delete_node(match_spec)
    
    def test_delete_edge_removes_edge_only(self, mock_memgraph_store):
        """Test that delete_edge removes only the edge, not connected nodes."""
        mock_memgraph_store._db.execute_and_fetch.return_value = [{"deleted_count": 1}]
        
        match_spec = MatchSpec(label="KNOWS")
        mock_memgraph_store.delete_edge(match_spec)
        
        # Verify the query was called
        mock_memgraph_store._db.execute_and_fetch.assert_called_once()
        call_args = mock_memgraph_store._db.execute_and_fetch.call_args
        query = call_args[0][0]
        assert "DELETE r" in query
        assert "DETACH DELETE" not in query
    
    def test_delete_edge_no_matches_raises_error(self, mock_memgraph_store):
        """Test that delete_edge raises NotFoundError when no matches found."""
        mock_memgraph_store._db.execute_and_fetch.return_value = [{"deleted_count": 0}]
        
        match_spec = MatchSpec(label="Nonexistent")
        
        with pytest.raises(NotFoundError, match="No matching edges found"):
            mock_memgraph_store.delete_edge(match_spec)


class TestCypherQueryOperations:
    """Test Cypher query execution operations."""
    
    @pytest.fixture
    def mock_memgraph_store(self):
        """Create a MemgraphGraphStore with mocked database."""
        with patch('puntini.graph.memgraph_graph.Memgraph') as mock_memgraph_class:
            mock_db = Mock()
            mock_db.execute_and_fetch.return_value = [{"result": 1}]
            mock_memgraph_class.return_value = mock_db
            
            store = MemgraphGraphStore()
            store._db = mock_db
            return store
    
    def test_run_cypher_executes_query_with_params(self, mock_memgraph_store):
        """Test that run_cypher executes query with parameters."""
        mock_results = [{"n": {"id": "1", "name": "test"}}]
        mock_memgraph_store._db.execute_and_fetch.return_value = mock_results
        
        query = "MATCH (n:Person) RETURN n"
        params = {"name": "John"}
        
        result = mock_memgraph_store.run_cypher(query, params)
        
        assert result == mock_results
        mock_memgraph_store._db.execute_and_fetch.assert_called_once_with(query, name="John")
    
    def test_run_cypher_executes_query_without_params(self, mock_memgraph_store):
        """Test that run_cypher executes query without parameters."""
        mock_results = [{"n": {"id": "1", "name": "test"}}]
        mock_memgraph_store._db.execute_and_fetch.return_value = mock_results
        
        query = "MATCH (n:Person) RETURN n"
        
        result = mock_memgraph_store.run_cypher(query)
        
        assert result == mock_results
        mock_memgraph_store._db.execute_and_fetch.assert_called_once_with(query)
    
    def test_run_cypher_handles_database_error(self, mock_memgraph_store):
        """Test that run_cypher handles database errors correctly."""
        mock_memgraph_store._db.execute_and_fetch.side_effect = Exception("Query failed")
        
        query = "INVALID QUERY"
        
        with pytest.raises(QueryError, match="Database error"):
            mock_memgraph_store.run_cypher(query)
    
    def test_run_cypher_handles_validation_error(self, mock_memgraph_store):
        """Test that run_cypher handles validation errors correctly."""
        mock_memgraph_store._db.execute_and_fetch.side_effect = Exception("Validation failed")
        
        query = "MATCH (n:Person) RETURN n"
        
        with pytest.raises(ValidationError, match="Validation error"):
            mock_memgraph_store.run_cypher(query)


class TestSubgraphOperations:
    """Test subgraph retrieval operations."""
    
    @pytest.fixture
    def mock_memgraph_store(self):
        """Create a MemgraphGraphStore with mocked database."""
        with patch('puntini.graph.memgraph_graph.Memgraph') as mock_memgraph_class:
            mock_db = Mock()
            mock_db.execute_and_fetch.return_value = [{"result": 1}]
            mock_memgraph_class.return_value = mock_db
            
            store = MemgraphGraphStore()
            store._db = mock_db
            return store
    
    def test_get_subgraph_returns_subgraph_data(self, mock_memgraph_store):
        """Test that get_subgraph returns properly formatted subgraph data."""
        # Mock database response
        mock_node_data = {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "label": "Person",
            "key": "john_doe",
            "name": "John Doe"
        }
        mock_edge_data = {
            "id": "550e8400-e29b-41d4-a716-446655440001",
            "type": "KNOWS",
            "start_node": mock_node_data,
            "end_node": mock_node_data
        }
        
        mock_memgraph_store._db.execute_and_fetch.return_value = [{
            "nodes": [mock_node_data],
            "edges": [mock_edge_data]
        }]
        
        match_spec = MatchSpec(label="Person", key="john_doe")
        subgraph = mock_memgraph_store.get_subgraph(match_spec, depth=1)
        
        assert isinstance(subgraph, dict)
        assert "nodes" in subgraph
        assert "edges" in subgraph
        assert "depth" in subgraph
        assert "central_nodes" in subgraph
        assert subgraph["depth"] == 1
    
    def test_get_subgraph_no_matches_raises_error(self, mock_memgraph_store):
        """Test that get_subgraph raises NotFoundError when no matches found."""
        mock_memgraph_store._db.execute_and_fetch.return_value = []  # Empty result
        
        match_spec = MatchSpec(label="Nonexistent")
        
        with pytest.raises(NotFoundError, match="No matching nodes found"):
            mock_memgraph_store.get_subgraph(match_spec)
    
    def test_get_subgraph_negative_depth_raises_error(self, mock_memgraph_store):
        """Test that get_subgraph raises ValidationError for negative depth."""
        match_spec = MatchSpec(label="Person", key="john_doe")
        
        with pytest.raises(ValidationError, match="Depth must be non-negative"):
            mock_memgraph_store.get_subgraph(match_spec, depth=-1)
    
    def test_get_subgraph_validation_error_empty_match_spec(self, mock_memgraph_store):
        """Test that get_subgraph raises ValidationError for empty match specification."""
        match_spec = MatchSpec()  # No criteria specified
        
        with pytest.raises(ValidationError, match="Match specification must include at least one criteria"):
            mock_memgraph_store.get_subgraph(match_spec)


class TestMatchingOperations:
    """Test internal matching operations."""
    
    @pytest.fixture
    def mock_memgraph_store(self):
        """Create a MemgraphGraphStore with mocked database."""
        with patch('puntini.graph.memgraph_graph.Memgraph') as mock_memgraph_class:
            mock_db = Mock()
            mock_db.execute_and_fetch.return_value = [{"result": 1}]
            mock_memgraph_class.return_value = mock_db
            
            store = MemgraphGraphStore()
            store._db = mock_db
            return store
    
    def test_matches_central_criteria_by_id(self, mock_memgraph_store):
        """Test that _matches_central_criteria works correctly with ID matching."""
        node_data = {"id": "550e8400-e29b-41d4-a716-446655440000", "labels": ["Person"], "key": "john_doe"}
        match_spec = MatchSpec(id=UUID("550e8400-e29b-41d4-a716-446655440000"))
        
        assert mock_memgraph_store._matches_central_criteria(node_data, match_spec)
        
        # Test with different ID
        match_spec_different = MatchSpec(id=UUID("00000000-0000-0000-0000-000000000000"))
        assert not mock_memgraph_store._matches_central_criteria(node_data, match_spec_different)
    
    def test_matches_central_criteria_by_label(self, mock_memgraph_store):
        """Test that _matches_central_criteria works correctly with label matching."""
        node_data = {"id": "1", "labels": ["Person"], "key": "john_doe"}
        match_spec = MatchSpec(label="Person")
        
        assert mock_memgraph_store._matches_central_criteria(node_data, match_spec)
        
        # Test with different label
        match_spec_different = MatchSpec(label="Company")
        assert not mock_memgraph_store._matches_central_criteria(node_data, match_spec_different)
    
    def test_matches_central_criteria_by_key(self, mock_memgraph_store):
        """Test that _matches_central_criteria works correctly with key matching."""
        node_data = {"id": "1", "labels": ["Person"], "key": "john_doe"}
        match_spec = MatchSpec(key="john_doe")
        
        assert mock_memgraph_store._matches_central_criteria(node_data, match_spec)
        
        # Test with different key
        match_spec_different = MatchSpec(key="jane_smith")
        assert not mock_memgraph_store._matches_central_criteria(node_data, match_spec_different)
    
    def test_matches_central_criteria_by_properties(self, mock_memgraph_store):
        """Test that _matches_central_criteria works correctly with property matching."""
        node_data = {"id": "1", "labels": ["Person"], "key": "john_doe", "name": "John Doe"}
        match_spec = MatchSpec(properties={"name": "John Doe"})
        
        assert mock_memgraph_store._matches_central_criteria(node_data, match_spec)
        
        # Test with non-matching property
        match_spec_different = MatchSpec(properties={"name": "Jane Smith"})
        assert not mock_memgraph_store._matches_central_criteria(node_data, match_spec_different)


class TestConnectionManagement:
    """Test connection management operations."""
    
    @patch('puntini.graph.memgraph_graph.Memgraph')
    def test_close_connection(self, mock_memgraph_class):
        """Test that close properly closes the database connection."""
        mock_db = Mock()
        mock_db.execute_and_fetch.return_value = [{"result": 1}]
        mock_memgraph_class.return_value = mock_db
        
        store = MemgraphGraphStore()
        
        # Test close method exists and can be called
        store.close()
        
        # If close method exists on the mock, verify it was called
        if hasattr(mock_db, 'close'):
            mock_db.close.assert_called_once()


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
    
    def test_query_error_inheritance(self):
        """Test that QueryError inherits from AgentError."""
        from puntini.models.errors import QueryError, AgentError
        
        error = QueryError("Test message")
        assert isinstance(error, AgentError)
        assert error.message == "Test message"
    
    def test_constraint_violation_error_inheritance(self):
        """Test that ConstraintViolationError inherits from AgentError."""
        from puntini.models.errors import ConstraintViolationError, AgentError
        
        error = ConstraintViolationError("Test message")
        assert isinstance(error, AgentError)
        assert error.message == "Test message"


class TestIdempotency:
    """Test idempotency guarantees of operations."""
    
    @pytest.fixture
    def mock_memgraph_store(self):
        """Create a MemgraphGraphStore with mocked database."""
        with patch('puntini.graph.memgraph_graph.Memgraph') as mock_memgraph_class:
            mock_db = Mock()
            mock_db.execute_and_fetch.return_value = [{"result": 1}]
            mock_memgraph_class.return_value = mock_db
            
            store = MemgraphGraphStore()
            store._db = mock_db
            return store
    
    def test_upsert_node_uses_merge_semantics(self, mock_memgraph_store):
        """Test that upsert_node uses MERGE semantics for idempotency."""
        mock_node_data = {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "label": "Person",
            "key": "john_doe",
            "name": "John Doe"
        }
        mock_memgraph_store._db.execute_and_fetch.return_value = [{"n": mock_node_data}]
        
        node_spec = NodeSpec(
            label="Person",
            key="john_doe",
            properties={"name": "John Doe"}
        )
        
        # First call
        node1 = mock_memgraph_store.upsert_node(node_spec)
        
        # Second call with same spec (should be idempotent)
        node2 = mock_memgraph_store.upsert_node(node_spec)
        
        # Verify MERGE query was used
        calls = mock_memgraph_store._db.execute_and_fetch.call_args_list
        for call in calls:
            query = call[0][0]
            assert "MERGE" in query
            assert "ON CREATE" in query
            assert "ON MATCH" in query
    
    def test_upsert_edge_uses_merge_semantics(self, mock_memgraph_store):
        """Test that upsert_edge uses MERGE semantics for idempotency."""
        mock_edge_data = {
            "id": "550e8400-e29b-41d4-a716-446655440001",
            "relationship_type": "KNOWS",
            "source_key": "john_doe",
            "target_key": "jane_smith"
        }
        mock_source_data = {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "label": "Person",
            "key": "john_doe"
        }
        mock_target_data = {
            "id": "550e8400-e29b-41d4-a716-446655440002",
            "label": "Person",
            "key": "jane_smith"
        }
        
        mock_memgraph_store._db.execute_and_fetch.return_value = [{
            "r": mock_edge_data,
            "source": mock_source_data,
            "target": mock_target_data
        }]
        
        edge_spec = EdgeSpec(
            relationship_type="KNOWS",
            source_key="john_doe",
            target_key="jane_smith",
            source_label="Person",
            target_label="Person"
        )
        
        # First call
        edge1 = mock_memgraph_store.upsert_edge(edge_spec)
        
        # Second call with same spec (should be idempotent)
        edge2 = mock_memgraph_store.upsert_edge(edge_spec)
        
        # Verify MERGE query was used
        calls = mock_memgraph_store._db.execute_and_fetch.call_args_list
        for call in calls:
            query = call[0][0]
            assert "MERGE" in query
            assert "ON CREATE" in query
            assert "ON MATCH" in query
