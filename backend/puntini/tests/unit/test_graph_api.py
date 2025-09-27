"""Unit tests for graph API endpoints."""

import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

from puntini.api.app import create_app
from puntini.api.auth import get_current_user
from puntini.api.models import GraphDataResponse, GraphNodeResponse, GraphEdgeResponse
from puntini.graph.in_memory_graph import InMemoryGraphStore
from puntini.models.node import Node
from puntini.models.edge import Edge
from puntini.models.specs import NodeSpec, EdgeSpec


class TestGraphAPI:
    """Test cases for graph API endpoints."""

    @pytest.fixture
    def app(self):
        """Create test FastAPI app."""
        app = create_app()
        
        # Override the auth dependency for testing
        def override_get_current_user():
            return "test_user"
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_graph_store(self):
        """Create mock graph store with test data."""
        store = InMemoryGraphStore()
        
        # Add test nodes
        node1 = store.upsert_node(NodeSpec(
            label="Person",
            key="john_doe",
            properties={"name": "John Doe", "age": 30}
        ))
        
        node2 = store.upsert_node(NodeSpec(
            label="Company",
            key="acme_corp",
            properties={"name": "Acme Corp", "industry": "Technology"}
        ))
        
        # Add test edge
        store.upsert_edge(EdgeSpec(
            relationship_type="WORKS_FOR",
            source_label="Person",
            source_key="john_doe",
            target_label="Company",
            target_key="acme_corp",
            properties={"position": "Engineer", "start_date": "2023-01-01"}
        ))
        
        return store

    @patch('puntini.api.app.make_graph_store')
    @patch('puntini.api.app.Settings')
    def test_get_graph_data_success(self, mock_settings, mock_make_graph_store, client, mock_graph_store):
        """Test successful graph data retrieval."""
        # Setup mocks
        mock_settings.return_value.get_graph_store_config.return_value = {"kind": "memory"}
        mock_make_graph_store.return_value = mock_graph_store
        
        # Make request
        response = client.get("/graph")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        assert "nodes" in data
        assert "edges" in data
        assert "total_nodes" in data
        assert "total_edges" in data
        
        assert data["total_nodes"] == 2
        assert data["total_edges"] == 1
        assert len(data["nodes"]) == 2
        assert len(data["edges"]) == 1
        
        # Verify node structure
        node_data = data["nodes"][0]
        assert "id" in node_data
        assert "label" in node_data
        assert "key" in node_data
        assert "properties" in node_data
        
        # Verify edge structure
        edge_data = data["edges"][0]
        assert "id" in edge_data
        assert "relationship_type" in edge_data
        assert "source_id" in edge_data
        assert "target_id" in edge_data

    @patch('puntini.api.app.make_graph_store')
    @patch('puntini.api.app.Settings')
    def test_get_graph_data_error(self, mock_settings, mock_make_graph_store, client):
        """Test graph data retrieval error handling."""
        # Setup mocks to raise exception
        mock_settings.return_value.get_graph_store_config.return_value = {"kind": "memory"}
        mock_make_graph_store.side_effect = Exception("Graph store error")
        
        # Make request
        response = client.get("/graph")
        
        # Verify error response
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Failed to retrieve graph data" in data["detail"]

    @patch('puntini.api.app.make_graph_store')
    @patch('puntini.api.app.Settings')
    def test_get_subgraph_success(self, mock_settings, mock_make_graph_store, client, mock_graph_store):
        """Test successful subgraph retrieval."""
        # Setup mocks
        mock_settings.return_value.get_graph_store_config.return_value = {"kind": "memory"}
        mock_make_graph_store.return_value = mock_graph_store
        
        # Make request
        request_data = {
            "match_spec": {"label": "Person"},
            "depth": 1
        }
        
        response = client.post("/graph/subgraph", json=request_data)
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        assert "nodes" in data
        assert "edges" in data
        assert "depth" in data
        assert "central_nodes" in data
        
        assert data["depth"] == 1
        assert len(data["central_nodes"]) == 1

    def test_get_graph_data_unauthorized(self):
        """Test graph data retrieval without authentication."""
        # Create app without auth override
        app = create_app()
        client = TestClient(app)
        response = client.get("/graph")
        assert response.status_code == 403  # FastAPI returns 403 for missing auth

    def test_get_subgraph_unauthorized(self):
        """Test subgraph retrieval without authentication."""
        # Create app without auth override
        app = create_app()
        client = TestClient(app)
        request_data = {
            "match_spec": {"label": "Person"},
            "depth": 1
        }
        
        response = client.post("/graph/subgraph", json=request_data)
        assert response.status_code == 403  # FastAPI returns 403 for missing auth
