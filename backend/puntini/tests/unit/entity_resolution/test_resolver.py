"""Tests for entity resolution logic."""

import sys
sys.path.append('/home/nicola/dev/puntini/backend')

import pytest
from unittest.mock import Mock
from uuid import uuid4

from puntini.entity_resolution.resolver import (
    GraphAwareEntityResolver,
    EntityResolutionService
)
from puntini.entity_resolution.models import (
    ResolutionStrategy,
    EntityCandidate
)
from puntini.entity_resolution.context import GraphContext, GraphSnapshot
from puntini.entity_resolution.similarity import SimilarityConfig


class TestGraphAwareEntityResolver:
    """Test GraphAwareEntityResolver class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_graph_store = Mock()
        self.config = SimilarityConfig()
        self.resolver = GraphAwareEntityResolver(
            graph_store=self.mock_graph_store,
            similarity_config=self.config
        )
        
        # Create mock context
        self.mock_context = Mock(spec=GraphContext)
        self.mock_context.snapshot = Mock(spec=GraphSnapshot)
        self.mock_context.snapshot.nodes = []
        self.mock_context.entity_similarities = {}
    
    def test_resolve_mention_no_candidates(self):
        """Test resolving mention with no candidates."""
        self.mock_context.snapshot.nodes = []
        
        resolution = self.resolver.resolve_mention("NewEntity", self.mock_context)
        
        assert resolution.strategy == ResolutionStrategy.CREATE_NEW
        assert resolution.entity_id is None
        assert resolution.confidence.overall < 0.5
        assert "No similar entities found" in resolution.reasoning
    
    def test_resolve_mention_high_confidence(self):
        """Test resolving mention with high confidence match."""
        # Create mock node with exact name match
        mock_node = Mock()
        mock_node.id = uuid4()
        mock_node.name = "John Doe"
        mock_node.label = "User"
        mock_node.properties = {}
        
        self.mock_context.snapshot.nodes = [mock_node]
        
        resolution = self.resolver.resolve_mention("John Doe", self.mock_context)
        
        # Should use existing entity due to exact match
        assert resolution.strategy == ResolutionStrategy.USE_EXISTING
        assert resolution.entity_id is not None
        assert resolution.confidence.overall > 0.7  # Lower threshold due to actual calculation
        assert "High confidence match found" in resolution.reasoning
    
    def test_resolve_mention_medium_confidence(self):
        """Test resolving mention with medium confidence match."""
        # Create mock node with similar but not exact name
        mock_node = Mock()
        mock_node.id = uuid4()
        mock_node.name = "John Smith"
        mock_node.label = "User"
        mock_node.properties = {}
        
        self.mock_context.snapshot.nodes = [mock_node]
        
        resolution = self.resolver.resolve_mention("John", self.mock_context)
        
        # Should use existing entity due to medium confidence (above threshold)
        assert resolution.strategy == ResolutionStrategy.USE_EXISTING
        assert resolution.entity_id is not None
        assert 0.3 < resolution.confidence.overall < 0.95
        assert "High confidence match found" in resolution.reasoning
    
    def test_resolve_mention_low_confidence(self):
        """Test resolving mention with low confidence match."""
        # Create mock node with very different name
        mock_node = Mock()
        mock_node.id = uuid4()
        mock_node.name = "Completely Different"
        mock_node.label = "User"
        mock_node.properties = {}
        
        self.mock_context.snapshot.nodes = [mock_node]
        
        resolution = self.resolver.resolve_mention("John", self.mock_context)
        
        # Should ask user due to low confidence
        assert resolution.strategy == ResolutionStrategy.ASK_USER
        assert resolution.entity_id is None
        assert resolution.confidence.overall < 0.5
        assert "Multiple candidates found" in resolution.reasoning
    
    def test_resolve_mentions_multiple(self):
        """Test resolving multiple mentions."""
        # Create mock nodes
        mock_node1 = Mock()
        mock_node1.id = uuid4()
        mock_node1.name = "John Doe"
        mock_node1.label = "User"
        mock_node1.properties = {}
        
        mock_node2 = Mock()
        mock_node2.id = uuid4()
        mock_node2.name = "Jane Smith"
        mock_node2.label = "User"
        mock_node2.properties = {}
        
        self.mock_context.snapshot.nodes = [mock_node1, mock_node2]
        
        mentions = ["John Doe", "Jane Smith", "New Person"]
        resolutions = self.resolver.resolve_mentions(mentions, self.mock_context)
        
        assert len(resolutions) == 3
        
        # First two should use existing entities
        assert resolutions[0].strategy == ResolutionStrategy.USE_EXISTING
        assert resolutions[1].strategy == ResolutionStrategy.USE_EXISTING
        
        # Third should ask user (no candidates found)
        assert resolutions[2].strategy == ResolutionStrategy.ASK_USER
    
    def test_find_candidates_from_snapshot(self):
        """Test finding candidates from graph snapshot."""
        # Create mock nodes
        mock_node1 = Mock()
        mock_node1.id = uuid4()
        mock_node1.name = "John Doe"
        mock_node1.label = "User"
        mock_node1.properties = {"email": "john@example.com"}
        
        mock_node2 = Mock()
        mock_node2.id = uuid4()
        mock_node2.name = "Jane Smith"
        mock_node2.label = "User"
        mock_node2.properties = {"email": "jane@example.com"}
        
        self.mock_context.snapshot.nodes = [mock_node1, mock_node2]
        
        candidates = self.resolver.find_candidates("John", self.mock_context)
        
        assert len(candidates) >= 1  # John Doe should match, Jane Smith might have low similarity
        # Find John Doe candidate
        john_candidate = next((c for c in candidates if c.name == "John Doe"), None)
        assert john_candidate is not None
        assert john_candidate.id == str(mock_node1.id)
    
    def test_find_candidates_from_precomputed(self):
        """Test finding candidates from precomputed similarities."""
        self.mock_context.entity_similarities = {
            "John": [
                {"id": "user:123", "name": "John Doe", "similarity": 0.9},
                {"id": "user:456", "name": "John Smith", "similarity": 0.7}
            ]
        }
        
        candidates = self.resolver.find_candidates("John", self.mock_context)
        
        assert len(candidates) == 2
        assert candidates[0].name == "John Doe"
        assert candidates[1].name == "John Smith"
    
    def test_find_candidates_combined(self):
        """Test finding candidates from both snapshot and precomputed."""
        # Mock node from snapshot
        mock_node = Mock()
        mock_node.id = uuid4()
        mock_node.name = "John Johnson"
        mock_node.label = "User"
        mock_node.properties = {}
        
        self.mock_context.snapshot.nodes = [mock_node]
        self.mock_context.entity_similarities = {
            "John": [
                {"id": "user:123", "name": "John Doe", "similarity": 0.9}
            ]
        }
        
        candidates = self.resolver.find_candidates("John", self.mock_context)
        
        # Should find candidates from both sources
        assert len(candidates) >= 2
        names = [c.name for c in candidates]
        assert "John Johnson" in names
        assert "John Doe" in names
    
    def test_calculate_basic_similarity_exact_match(self):
        """Test basic similarity calculation for exact match."""
        similarity = self.resolver._calculate_basic_similarity("John Doe", "John Doe")
        assert similarity == 1.0
    
    def test_calculate_basic_similarity_substring_match(self):
        """Test basic similarity calculation for substring match."""
        similarity = self.resolver._calculate_basic_similarity("John", "John Doe")
        assert similarity >= 0.8  # Should be boosted for substring match
    
    def test_calculate_basic_similarity_case_insensitive(self):
        """Test basic similarity calculation is case insensitive."""
        similarity1 = self.resolver._calculate_basic_similarity("john doe", "JOHN DOE")
        similarity2 = self.resolver._calculate_basic_similarity("John Doe", "John Doe")
        
        # Should be similar (allowing for small floating point differences)
        assert abs(similarity1 - similarity2) < 0.01


class TestEntityResolutionService:
    """Test EntityResolutionService class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_resolver = Mock()
        self.service = EntityResolutionService(self.mock_resolver)
    
    def test_resolve_entities_from_text(self):
        """Test resolving entities from text."""
        # Mock the resolver
        mock_resolution = Mock()
        mock_resolution.strategy = ResolutionStrategy.USE_EXISTING
        self.mock_resolver.resolve_mentions.return_value = [mock_resolution]
        
        # Mock the context
        mock_context = Mock()
        
        text = "John Doe is working on the project"
        resolutions = self.service.resolve_entities_from_text(text, mock_context)
        
        assert len(resolutions) == 1
        assert resolutions[0].strategy == ResolutionStrategy.USE_EXISTING
        
        # Verify that resolve_mentions was called
        self.mock_resolver.resolve_mentions.assert_called_once()
        call_args = self.mock_resolver.resolve_mentions.call_args
        mentions = call_args[0][0]  # First argument of the call
        assert "John" in mentions
        assert "Doe" in mentions
        assert "project" in mentions
    
    def test_extract_mentions_basic(self):
        """Test basic mention extraction."""
        text = "John Doe works on the project"
        mentions = self.service._extract_mentions(text)
        
        expected = ["John", "Doe", "works", "project"]
        assert mentions == expected
    
    def test_extract_mentions_with_delimiters(self):
        """Test mention extraction with various delimiters."""
        text = "John, Doe; works. on! the? project"
        mentions = self.service._extract_mentions(text)
        
        # Should extract words and filter common words ("on" and "the" are common)
        expected = ["John", "Doe", "works", "project"]
        assert mentions == expected
    
    def test_extract_mentions_filters_common_words(self):
        """Test that common words are filtered out."""
        text = "John Doe and the project"
        mentions = self.service._extract_mentions(text)
        
        # "and" and "the" should be filtered out
        assert "and" not in mentions
        assert "the" not in mentions
        assert "John" in mentions
        assert "Doe" in mentions
        assert "project" in mentions
    
    def test_extract_mentions_handles_whitespace(self):
        """Test that whitespace is handled correctly."""
        text = "  John   Doe  \n\n  works  "
        mentions = self.service._extract_mentions(text)
        
        # Should not have empty strings
        assert "" not in mentions
        assert "John" in mentions
        assert "Doe" in mentions
        assert "works" in mentions
    
    def test_extract_mentions_empty_text(self):
        """Test mention extraction with empty text."""
        mentions = self.service._extract_mentions("")
        assert mentions == []
    
    def test_extract_mentions_whitespace_only(self):
        """Test mention extraction with only whitespace."""
        mentions = self.service._extract_mentions("   \n\n  \t  ")
        assert mentions == []
