"""Tests for entity similarity scoring."""

import sys
sys.path.append('/home/nicola/dev/puntini/backend')

import pytest
from unittest.mock import Mock

from puntini.entity_resolution.similarity import (
    SimilarityConfig,
    EntitySimilarityScorer
)
from puntini.entity_resolution.models import EntityCandidate
from puntini.entity_resolution.context import GraphContext, GraphSnapshot


class TestSimilarityConfig:
    """Test SimilarityConfig model."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = SimilarityConfig()
        
        assert config.name_weight == 0.4
        assert config.type_weight == 0.3
        assert config.property_weight == 0.2
        assert config.context_weight == 0.1
        assert config.min_similarity_threshold == 0.3
        assert config.max_candidates == 10
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = SimilarityConfig(
            name_weight=0.5,
            type_weight=0.2,
            property_weight=0.2,
            context_weight=0.1,
            min_similarity_threshold=0.4,
            max_candidates=5
        )
        
        assert config.name_weight == 0.5
        assert config.type_weight == 0.2
        assert config.property_weight == 0.2
        assert config.context_weight == 0.1
        assert config.min_similarity_threshold == 0.4
        assert config.max_candidates == 5


class TestEntitySimilarityScorer:
    """Test EntitySimilarityScorer class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = SimilarityConfig()
        self.scorer = EntitySimilarityScorer(self.config)
        
        # Create mock context
        self.mock_context = Mock(spec=GraphContext)
        self.mock_context.snapshot = Mock(spec=GraphSnapshot)
        self.mock_context.snapshot.nodes = []
        self.mock_context.schema_info = {}
    
    def test_score_mention_candidates_empty(self):
        """Test scoring with empty candidates list."""
        candidates = []
        scored = self.scorer.score_mention_candidates(
            "John Doe", candidates, self.mock_context
        )
        
        assert len(scored) == 0
    
    def test_score_mention_candidates_single(self):
        """Test scoring with single candidate."""
        candidate = EntityCandidate(
            id="user:123",
            name="John Doe",
            label="User",
            similarity=0.0,  # Will be recalculated
            properties={"email": "john@example.com"}
        )
        
        candidates = [candidate]
        scored = self.scorer.score_mention_candidates(
            "John Doe", candidates, self.mock_context
        )
        
        assert len(scored) == 1
        assert scored[0].id == "user:123"
        assert scored[0].similarity > 0.0  # Should be recalculated
    
    def test_score_mention_candidates_multiple(self):
        """Test scoring with multiple candidates."""
        candidate1 = EntityCandidate(
            id="user:123",
            name="John Doe",
            label="User",
            similarity=0.0,
            properties={"email": "john@example.com"}
        )
        
        candidate2 = EntityCandidate(
            id="user:456",
            name="John Smith",
            label="User",
            similarity=0.0,
            properties={"email": "john.smith@example.com"}
        )
        
        candidates = [candidate1, candidate2]
        scored = self.scorer.score_mention_candidates(
            "John Doe", candidates, self.mock_context
        )
        
        assert len(scored) == 2
        # Should be sorted by similarity (highest first)
        assert scored[0].similarity >= scored[1].similarity
    
    def test_score_mention_candidates_threshold_filtering(self):
        """Test threshold filtering of candidates."""
        config = SimilarityConfig(min_similarity_threshold=0.5)
        scorer = EntitySimilarityScorer(config)
        
        candidate1 = EntityCandidate(
            id="user:123",
            name="John Doe",
            similarity=0.0,
            properties={}
        )
        
        candidate2 = EntityCandidate(
            id="user:456",
            name="Completely Different",
            similarity=0.0,
            properties={}
        )
        
        candidates = [candidate1, candidate2]
        scored = scorer.score_mention_candidates(
            "John Doe", candidates, self.mock_context
        )
        
        # Only high similarity candidates should pass threshold
        for candidate in scored:
            assert candidate.similarity >= 0.5
    
    def test_score_mention_candidates_max_limit(self):
        """Test maximum candidates limit."""
        config = SimilarityConfig(max_candidates=2)
        scorer = EntitySimilarityScorer(config)
        
        candidates = []
        for i in range(5):
            candidate = EntityCandidate(
                id=f"user:{i}",
                name=f"John Doe {i}",
                similarity=0.0,
                properties={}
            )
            candidates.append(candidate)
        
        scored = scorer.score_mention_candidates(
            "John Doe", candidates, self.mock_context
        )
        
        assert len(scored) <= 2
    
    def test_calculate_name_similarity_exact_match(self):
        """Test name similarity for exact match."""
        similarity = self.scorer._calculate_name_similarity("John Doe", "John Doe")
        assert similarity == 1.0
    
    def test_calculate_name_similarity_substring_match(self):
        """Test name similarity for substring match."""
        similarity = self.scorer._calculate_name_similarity("John", "John Doe")
        assert similarity >= 0.8  # Should be boosted for substring match
    
    def test_calculate_name_similarity_case_insensitive(self):
        """Test name similarity is case insensitive."""
        similarity1 = self.scorer._calculate_name_similarity("john doe", "JOHN DOE")
        similarity2 = self.scorer._calculate_name_similarity("John Doe", "John Doe")
        
        # Should be similar (allowing for small floating point differences)
        assert abs(similarity1 - similarity2) < 0.01
    
    def test_calculate_name_similarity_whitespace_insensitive(self):
        """Test name similarity handles whitespace differences."""
        similarity1 = self.scorer._calculate_name_similarity("John  Doe", "John Doe")
        similarity2 = self.scorer._calculate_name_similarity("John Doe", "John Doe")
        
        # Should be similar (allowing for small floating point differences)
        assert abs(similarity1 - similarity2) < 0.01
    
    def test_calculate_name_similarity_special_characters(self):
        """Test name similarity with special characters."""
        similarity = self.scorer._calculate_name_similarity("John-Doe!", "John Doe")
        
        # Should have reasonable similarity
        assert similarity > 0.0
        assert similarity < 1.0
    
    def test_calculate_type_similarity_with_label(self):
        """Test type similarity when candidate has label."""
        candidate = EntityCandidate(
            id="user:123",
            name="John Doe",
            label="User",
            similarity=0.0,
            properties={}
        )
        
        similarity = self.scorer._calculate_type_similarity(
            "John Doe", candidate, self.mock_context
        )
        
        assert similarity == 0.8  # Should return base score for labeled entity
    
    def test_calculate_type_similarity_without_label(self):
        """Test type similarity when candidate has no label."""
        candidate = EntityCandidate(
            id="user:123",
            name="John Doe",
            label=None,
            similarity=0.0,
            properties={}
        )
        
        similarity = self.scorer._calculate_type_similarity(
            "John Doe", candidate, self.mock_context
        )
        
        assert similarity == 0.5  # Should return lower score for unlabeled entity
    
    def test_calculate_property_similarity_no_properties(self):
        """Test property similarity with no properties."""
        candidate = EntityCandidate(
            id="user:123",
            name="John Doe",
            similarity=0.0,
            properties={}
        )
        
        similarity = self.scorer._calculate_property_similarity(
            "John Doe", candidate, self.mock_context
        )
        
        assert similarity == 0.0  # Should return 0 for no properties
    
    def test_calculate_property_similarity_with_properties(self):
        """Test property similarity with matching properties."""
        candidate = EntityCandidate(
            id="user:123",
            name="John Doe",
            similarity=0.0,
            properties={"email": "john@example.com", "role": "developer"}
        )
        
        # Mock the property extraction to return matching properties
        self.scorer._extract_properties_from_mention = Mock(return_value={
            "email": "john@example.com"
        })
        
        similarity = self.scorer._calculate_property_similarity(
            "john@example.com", candidate, self.mock_context
        )
        
        assert similarity > 0.0  # Should have positive similarity for matching properties
    
    def test_calculate_context_similarity(self):
        """Test context similarity calculation."""
        candidate = EntityCandidate(
            id="user:123",
            name="John Doe",
            similarity=0.0,
            properties={}
        )
        
        similarity = self.scorer._calculate_context_similarity(
            "John Doe", candidate, self.mock_context
        )
        
        assert similarity == 0.5  # Should return base score for now
    
    def test_normalize_string(self):
        """Test string normalization."""
        # Test case normalization
        assert self.scorer._normalize_string("John Doe") == "john doe"
        
        # Test whitespace normalization
        assert self.scorer._normalize_string("  John   Doe  ") == "john doe"
        
        # Test special character removal
        assert self.scorer._normalize_string("John-Doe!") == "johndoe"
        
        # Test multiple special characters
        assert self.scorer._normalize_string("John@Doe#123") == "johndoe123"
    
    def test_extract_properties_from_mention_email(self):
        """Test property extraction for email addresses."""
        properties = self.scorer._extract_properties_from_mention("Contact john@example.com")
        assert "email" in properties
        assert properties["email"] == "john@example.com"
    
    def test_extract_properties_from_mention_id(self):
        """Test property extraction for ID patterns."""
        properties = self.scorer._extract_properties_from_mention("Ticket TICKET-123")
        assert "id" in properties
        assert properties["id"] == "TICKET-123"
    
    def test_extract_properties_from_mention_multiple(self):
        """Test property extraction for multiple patterns."""
        properties = self.scorer._extract_properties_from_mention(
            "Contact john@example.com about TICKET-123"
        )
        
        assert "email" in properties
        assert "id" in properties
        assert properties["email"] == "john@example.com"
        assert properties["id"] == "TICKET-123"
    
    def test_extract_properties_from_mention_none(self):
        """Test property extraction when no patterns match."""
        properties = self.scorer._extract_properties_from_mention("Just some text")
        assert properties == {}
