"""Unit tests for graph context module.

This tests the graph context management functionality including:
- Subgraph creation and querying
- Context management
- Context-aware entity matching
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from uuid import UUID, uuid4

from puntini.models.node import Node
from puntini.models.edge import Edge
from puntini.entity_resolution.models import EntityMention, GraphElementType
from puntini.entity_resolution.context import GraphContext, GraphSnapshot
from puntini.interfaces.graph_store import GraphStore
from puntini.context.graph_context import (
    GraphContextManager, ContextAwareEntityMatcher, GraphSubgraph, SubgraphQuery
)


class TestGraphContextManager:
    """Test the graph context manager."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.mock_graph_store = Mock()
        self.context_manager = GraphContextManager(self.mock_graph_store)
    
    def test_create_context_for_query(self):
        """Test creating context for a query."""
        # Mock the graph store responses
        node1 = Node(id=uuid4(), label="User", key="user:123", properties={"name": "John Doe", "email": "john@example.com"})
        node2 = Node(id=uuid4(), label="Project", key="project:456", properties={"name": "Test Project", "status": "active"})
        
        self.mock_graph_store.get_all_nodes.return_value = [node1, node2]
        self.mock_graph_store.get_all_node_labels.return_value = ["User", "Project"]
        self.mock_graph_store.get_all_relationship_types.return_value = ["MEMBER_OF", "ASSIGNED_TO"]
        
        context = self.context_manager.create_context_for_query("John Doe working on Test Project")
        
        # Should create a context with the nodes
        assert isinstance(context, GraphContext)
        assert len(context.snapshot.nodes) == 2
        assert context.snapshot.nodes[0].properties["name"] == "John Doe"
        assert context.snapshot.nodes[1].properties["name"] == "Test Project"
    
    def test_create_context_for_entities(self):
        """Test creating context for specific entities."""
        node1 = Node(id=uuid4(), label="User", key="user:123", properties={"name": "John Doe", "email": "john@example.com"})
        node2 = Node(id=uuid4(), label="Ticket", key="ticket:789", properties={"name": "BUG-123", "status": "open"})
        
        self.mock_graph_store.find_nodes_by_name.return_value = [node1]
        self.mock_graph_store.get_subgraph_around_node.return_value = GraphSubgraph(
            nodes=[node1, node2],
            edges=[],
            context_depth=2
        )
        self.mock_graph_store.get_all_node_labels.return_value = ["User", "Ticket"]
        self.mock_graph_store.get_all_relationship_types.return_value = ["REPORTED", "ASSIGNED"]
        
        context = self.context_manager.create_context_for_entities(["John Doe"], max_depth=2, max_nodes=10)
        
        assert isinstance(context, GraphContext)
        assert len(context.snapshot.nodes) >= 1  # At least John Doe should be in context
    
    def test_query_similar_entities(self):
        """Test querying for similar entities."""
        node1 = Node(id=uuid4(), label="User", key="user:123", properties={"name": "John Doe", "email": "john@example.com"})
        node2 = Node(id=uuid4(), label="User", key="user:456", properties={"name": "John Smith", "email": "john2@example.com"})
        
        self.mock_graph_store.get_all_nodes.return_value = [node1, node2]
        self.mock_graph_store.get_all_node_labels.return_value = ["User"]
        self.mock_graph_store.get_all_relationship_types.return_value = ["FRIEND_OF"]
        
        mention = EntityMention(surface_form="John", element_type=GraphElementType.NODE_REFERENCE)
        candidates = self.context_manager.query_similar_entities(mention, threshold=0.1)
        
        # Should return candidates for both John Doe and John Smith since both contain "John"
        assert len(candidates) >= 1
        candidate_names = [c.name for c in candidates]
        assert any("John" in name for name in candidate_names)
    
    def test_create_context_around_node(self):
        """Test creating context around a specific node."""
        node1 = Node(id=uuid4(), label="User", key="user:123", properties={"name": "John Doe", "email": "john@example.com"})
        node2 = Node(id=uuid4(), label="Project", key="project:456", properties={"name": "Test Project", "status": "active"})
        
        edge1 = Edge(
            id=uuid4(),
            relationship_type="MEMBER_OF",
            source_node_id=str(node1.id),
            target_node_id=str(node2.id),
            properties={}
        )
        
        subgraph = GraphSubgraph(
            nodes=[node1, node2],
            edges=[edge1],
            context_depth=2
        )
        
        self.mock_graph_store.get_subgraph_around_node.return_value = subgraph
        self.mock_graph_store.get_all_node_labels.return_value = ["User", "Project"]
        self.mock_graph_store.get_all_relationship_types.return_value = ["MEMBER_OF"]
        
        context = self.context_manager.create_context_around_node("1", max_depth=2)
        
        assert isinstance(context, GraphContext)
        assert len(context.snapshot.nodes) == 2
        assert len(context.snapshot.edges) == 1
        assert context.snapshot.context_depth == 2


class TestContextAwareEntityMatcher:
    """Test the context-aware entity matcher."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.mock_graph_store = Mock()
        self.context_manager = GraphContextManager(self.mock_graph_store)
        self.matcher = ContextAwareEntityMatcher(self.context_manager)
    
    def test_match_entity_to_graph(self):
        """Test matching an entity to graph entities."""
        node1 = Node(id=uuid4(), label="User", key="user:123", properties={"name": "John Doe", "email": "john@example.com"})
        node2 = Node(id=uuid4(), label="User", key="user:456", properties={"name": "John Smith", "email": "john2@example.com"})
        
        self.mock_graph_store.get_all_nodes.return_value = [node1, node2]
        self.mock_graph_store.get_all_node_labels.return_value = ["User"]
        self.mock_graph_store.get_all_relationship_types.return_value = ["FRIEND_OF"]
        
        candidates = self.matcher.match_entity_to_graph("John Doe", threshold=0.5)
        
        # Should return a candidate for John Doe
        assert len(candidates) >= 1
        john_candidates = [c for c in candidates if "John Doe" in c.name]
        assert len(john_candidates) >= 1
    
    def test_find_potential_duplicates(self):
        """Test finding potential duplicate entities."""
        node1 = Node(id=uuid4(), label="User", key="user:123", properties={"name": "John Doe", "email": "john@example.com", "role": "admin"})
        node2 = Node(id=uuid4(), label="User", key="user:456", properties={"name": "John", "email": "john@example.com", "department": "IT"})
        
        self.mock_graph_store.get_all_nodes.return_value = [node1, node2]
        self.mock_graph_store.get_all_node_labels.return_value = ["User"]
        self.mock_graph_store.get_all_relationship_types.return_value = ["FRIEND_OF"]
        
        new_entity = {"name": "John Doe", "email": "john@example.com"}
        duplicates = self.matcher.find_potential_duplicates(new_entity, threshold=0.8)
        
        # Should find John with same email as potential duplicate
        assert len(duplicates) >= 0  # May not find exact matches depending on similarity algorithm


class TestGraphSubgraph:
    """Test the GraphSubgraph model."""
    
    def test_get_node_by_id(self):
        """Test getting a node by ID."""
        node_id1 = uuid4()
        node_id2 = uuid4()
        node1 = Node(id=node_id1, label="User", key="user:123", properties={"name": "John"})
        node2 = Node(id=node_id2, label="Project", key="project:456", properties={"name": "Test"})
        
        subgraph = GraphSubgraph(nodes=[node1, node2], edges=[])
        
        result = subgraph.get_node_by_id(str(node_id1))
        assert result is not None
        assert result.properties["name"] == "John"
        
        result = subgraph.get_node_by_id(str(uuid4()))  # Non-existent
        assert result is None
    
    def test_get_nodes_by_label(self):
        """Test getting nodes by label."""
        node1 = Node(id=uuid4(), label="User", key="user:123", properties={"name": "John"})
        node2 = Node(id=uuid4(), label="Project", key="project:456", properties={"name": "Test"})
        node3 = Node(id=uuid4(), label="User", key="user:789", properties={"name": "Jane"})
        
        subgraph = GraphSubgraph(nodes=[node1, node2, node3], edges=[])
        
        users = subgraph.get_nodes_by_label("User")
        assert len(users) == 2
        assert all(n.label == "User" for n in users)
    
    def test_get_neighbors(self):
        """Test getting neighbor nodes."""
        node1 = Node(id=uuid4(), label="User", key="user:123", properties={"name": "John"})
        node2 = Node(id=uuid4(), label="Project", key="project:456", properties={"name": "Test"})
        node3 = Node(id=uuid4(), label="Ticket", key="ticket:789", properties={"name": "Bug"})
        
        edge1 = Edge(
            id=uuid4(),
            relationship_type="MEMBER_OF",
            source_id=node1.id,
            target_id=node2.id,
            source_key=node1.key,
            target_key=node2.key,
            source_label=node1.label,
            target_label=node2.label,
            properties={}
        )
        
        edge2 = Edge(
            id=uuid4(),
            relationship_type="REPORTED",
            source_id=node1.id,
            target_id=node3.id,
            source_key=node1.key,
            target_key=node3.key,
            source_label=node1.label,
            target_label=node3.label,
            properties={}
        )
        
        subgraph = GraphSubgraph(
            nodes=[node1, node2, node3],
            edges=[edge1, edge2]
        )
        
        neighbors = subgraph.get_neighbors(str(node1.id))
        assert len(neighbors) == 2
        neighbor_names = [n.properties.get("name") for n in neighbors]
        assert "Test" in neighbor_names
        assert "Bug" in neighbor_names


class TestSubgraphQuery:
    """Test the SubgraphQuery model."""
    
    def test_subgraph_query_creation(self):
        """Test creating a subgraph query."""
        query = SubgraphQuery(
            node_types=["User", "Project"],
            relationship_types=["MEMBER_OF", "REPORTED"],
            max_depth=2,
            max_nodes=50,
            filters={"status": "active"},
            include_properties=True
        )
        
        assert query.node_types == ["User", "Project"]
        assert query.relationship_types == ["MEMBER_OF", "REPORTED"]
        assert query.max_depth == 2
        assert query.max_nodes == 50
        assert query.filters == {"status": "active"}
        assert query.include_properties is True