"""Tests for entity resolution context models."""

import sys
sys.path.append('/home/nicola/dev/puntini/backend')

import pytest
from uuid import uuid4
from datetime import datetime

from puntini.entity_resolution.context import GraphSnapshot, GraphContext
from puntini.models.node import Node
from puntini.models.edge import Edge


class TestGraphSnapshot:
    """Test GraphSnapshot model."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.node1 = Node(
            id=uuid4(),
            label="User",
            key="user:123",
            properties={"name": "John Doe", "email": "john@example.com"}
        )
        
        self.node2 = Node(
            id=uuid4(),
            label="Project",
            key="project:456",
            properties={"name": "Test Project", "status": "active"}
        )
        
        self.edge = Edge(
            id=uuid4(),
            relationship_type="MEMBER_OF",
            source_id=self.node1.id,
            target_id=self.node2.id,
            source_key=self.node1.key,
            target_key=self.node2.key,
            source_label=self.node1.label,
            target_label=self.node2.label,
            properties={"role": "developer"}
        )
    
    def test_create_snapshot(self):
        """Test creating a graph snapshot."""
        snapshot = GraphSnapshot(
            nodes=[self.node1, self.node2],
            edges=[self.edge],
            context_depth=2
        )
        
        assert len(snapshot.nodes) == 2
        assert len(snapshot.edges) == 1
        assert snapshot.context_depth == 2
        assert isinstance(snapshot.created_at, datetime)
    
    def test_get_node_by_id(self):
        """Test getting node by ID."""
        snapshot = GraphSnapshot(
            nodes=[self.node1, self.node2],
            edges=[]
        )
        
        found_node = snapshot.get_node_by_id(str(self.node1.id))
        assert found_node is not None
        assert found_node.id == self.node1.id
        assert found_node.properties["name"] == "John Doe"
        
        # Test with non-existent ID
        not_found = snapshot.get_node_by_id("non-existent")
        assert not_found is None
    
    def test_get_nodes_by_label(self):
        """Test getting nodes by label."""
        snapshot = GraphSnapshot(
            nodes=[self.node1, self.node2],
            edges=[]
        )
        
        user_nodes = snapshot.get_nodes_by_label("User")
        assert len(user_nodes) == 1
        assert user_nodes[0].id == self.node1.id
        
        project_nodes = snapshot.get_nodes_by_label("Project")
        assert len(project_nodes) == 1
        assert project_nodes[0].id == self.node2.id
        
        # Test with non-existent label
        empty_nodes = snapshot.get_nodes_by_label("NonExistent")
        assert len(empty_nodes) == 0
    
    def test_get_edges_by_type(self):
        """Test getting edges by type."""
        snapshot = GraphSnapshot(
            nodes=[],
            edges=[self.edge]
        )
        
        member_edges = snapshot.get_edges_by_type("MEMBER_OF")
        assert len(member_edges) == 1
        assert member_edges[0].id == self.edge.id
        
        # Test with non-existent type
        empty_edges = snapshot.get_edges_by_type("NON_EXISTENT")
        assert len(empty_edges) == 0
    
    def test_empty_snapshot(self):
        """Test creating empty snapshot."""
        snapshot = GraphSnapshot()
        
        assert len(snapshot.nodes) == 0
        assert len(snapshot.edges) == 0
        assert snapshot.context_depth == 1
        assert isinstance(snapshot.created_at, datetime)


class TestGraphContext:
    """Test GraphContext model."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.node1 = Node(
            id=uuid4(),
            label="User",
            key="user:123",
            properties={"name": "John Doe", "email": "john@example.com"}
        )
        
        self.node2 = Node(
            id=uuid4(),
            label="Project",
            key="project:456",
            properties={"name": "Test Project", "status": "active"}
        )
        
        self.snapshot = GraphSnapshot(
            nodes=[self.node1, self.node2],
            edges=[]
        )
    
    def test_create_context(self):
        """Test creating graph context."""
        context = GraphContext(
            snapshot=self.snapshot,
            entity_similarities={
                "John": [
                    {"id": "user:123", "name": "John Doe", "similarity": 0.9}
                ]
            },
            schema_info={
                "labels": ["User", "Project"],
                "relationship_types": ["MEMBER_OF", "ASSIGNED_TO"]
            }
        )
        
        assert context.snapshot == self.snapshot
        assert "John" in context.entity_similarities
        assert context.schema_info["labels"] == ["User", "Project"]
        assert context.user_context == {}
    
    def test_find_similar_entities(self):
        """Test finding similar entities."""
        context = GraphContext(
            snapshot=self.snapshot,
            entity_similarities={
                "John": [
                    {"id": "user:123", "name": "John Doe", "similarity": 0.9},
                    {"id": "user:456", "name": "John Smith", "similarity": 0.7}
                ]
            }
        )
        
        similar_entities = context.find_similar_entities("John")
        assert len(similar_entities) == 2
        assert similar_entities[0]["similarity"] == 0.9
        assert similar_entities[1]["similarity"] == 0.7
        
        # Test with threshold
        high_similarity = context.find_similar_entities("John", threshold=0.8)
        assert len(high_similarity) == 1
        assert high_similarity[0]["similarity"] == 0.9
    
    def test_find_similar_entities_nonexistent(self):
        """Test finding similar entities for nonexistent mention."""
        context = GraphContext(snapshot=self.snapshot)
        
        similar_entities = context.find_similar_entities("Nonexistent")
        assert len(similar_entities) == 0
    
    def test_get_schema_labels(self):
        """Test getting schema labels."""
        context = GraphContext(
            snapshot=self.snapshot,
            schema_info={
                "labels": ["User", "Project", "Task"],
                "relationship_types": ["MEMBER_OF"]
            }
        )
        
        labels = context.get_schema_labels()
        assert labels == ["User", "Project", "Task"]
    
    def test_get_schema_labels_empty(self):
        """Test getting schema labels when none exist."""
        context = GraphContext(snapshot=self.snapshot)
        
        labels = context.get_schema_labels()
        assert labels == []
    
    def test_get_relationship_types(self):
        """Test getting relationship types."""
        context = GraphContext(
            snapshot=self.snapshot,
            schema_info={
                "labels": ["User"],
                "relationship_types": ["MEMBER_OF", "ASSIGNED_TO", "DEPENDS_ON"]
            }
        )
        
        types = context.get_relationship_types()
        assert types == ["MEMBER_OF", "ASSIGNED_TO", "DEPENDS_ON"]
    
    def test_get_relationship_types_empty(self):
        """Test getting relationship types when none exist."""
        context = GraphContext(snapshot=self.snapshot)
        
        types = context.get_relationship_types()
        assert types == []
    
    def test_is_entity_in_context(self):
        """Test checking if entity is in context."""
        context = GraphContext(snapshot=self.snapshot)
        
        # Entity exists
        exists = context.is_entity_in_context(str(self.node1.id))
        assert exists is True
        
        # Entity doesn't exist
        not_exists = context.is_entity_in_context("non-existent-id")
        assert not_exists is False
    
    def test_empty_context(self):
        """Test creating empty context."""
        empty_snapshot = GraphSnapshot()
        context = GraphContext(snapshot=empty_snapshot)
        
        assert len(context.snapshot.nodes) == 0
        assert len(context.snapshot.edges) == 0
        assert context.entity_similarities == {}
        assert context.schema_info == {}
        assert context.user_context == {}
    
    def test_context_with_partial_data(self):
        """Test context with only some data provided."""
        context = GraphContext(
            snapshot=self.snapshot,
            user_context={"user_id": "123", "preferences": {"theme": "dark"}}
        )
        
        assert context.entity_similarities == {}
        assert context.schema_info == {}
        assert context.user_context["user_id"] == "123"
        assert context.user_context["preferences"]["theme"] == "dark"
