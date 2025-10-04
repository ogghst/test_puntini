"""Unit tests for entity resolution rules module.

This tests the entity resolution rules implementation including:
- Match rules for entity matching
- Merge strategies for duplicate handling
- Conflict resolution for property conflicts
- Entity deduplication engine
"""

import pytest
from unittest.mock import Mock, MagicMock
from typing import List

from puntini.entity_resolution.models import (
    EntityMention, EntityCandidate, ResolutionStrategy, GraphElementType
)
from puntini.entity_resolution.rules import (
    DefaultEntityResolutionRules, EntityDeduplicationEngine,
    MatchRule, MergeStrategy, ConflictResolution
)
from puntini.entity_resolution.similarity import EntitySimilarityScorer


class TestDefaultEntityResolutionRules:
    """Test the default entity resolution rules implementation."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.scorer = EntitySimilarityScorer()
        self.rules = DefaultEntityResolutionRules(similarity_scorer=self.scorer)
    
    def test_match_candidates_exact_key_match(self):
        """Test matching candidates by exact key (ID, email)."""
        mention = EntityMention(surface_form="john@example.com", element_type=GraphElementType.NODE_REFERENCE)
        
        candidates = [
            EntityCandidate(
                id="user:123",
                name="John Doe",
                similarity=0.9,
                properties={"email": "john@example.com", "role": "admin"}
            ),
            EntityCandidate(
                id="user:456", 
                name="Jane Smith",
                similarity=0.5,
                properties={"email": "jane@example.com", "role": "user"}
            )
        ]
        
        matches = self.rules.match_candidates(mention, candidates)
        
        # At least the exact match should be returned
        match_ids = [c.id for c in matches]
        assert "user:123" in match_ids  # The exact email match should be included
    
    def test_match_candidates_similar_name_match(self):
        """Test matching candidates by similar name."""
        mention = EntityMention(surface_form="John", element_type=GraphElementType.NODE_REFERENCE)
        
        candidates = [
            EntityCandidate(
                id="user:123",
                name="John Doe",
                similarity=0.8,
                properties={"email": "john@example.com"}
            ),
            EntityCandidate(
                id="user:456", 
                name="Jane Smith",
                similarity=0.6,
                properties={"email": "jane@example.com"}
            )
        ]
        
        matches = self.rules.match_candidates(mention, candidates)
        
        # Should match "John Doe" because "John" is part of "John Doe"
        assert len(matches) >= 1
        matched_ids = [c.id for c in matches]
        assert "user:123" in matched_ids
    
    def test_match_candidates_property_overlap_match(self):
        """Test matching candidates by property overlap."""
        mention = EntityMention(
            surface_form="John", 
            element_type=GraphElementType.NODE_REFERENCE,
            context={"email": "john@example.com", "role": "admin"}
        )
        
        candidates = [
            EntityCandidate(
                id="user:123",
                name="John Doe", 
                similarity=0.85,
                properties={"email": "john@example.com", "role": "admin", "department": "IT"}
            ),
            EntityCandidate(
                id="user:456",
                name="Jane Smith",
                similarity=0.6,
                properties={"email": "jane@example.com", "role": "user"}
            )
        ]
        
        matches = self.rules.match_candidates(mention, candidates)
        
        # Should match user:123 based on property overlap (email, role)
        assert len(matches) >= 1
        matched_ids = [c.id for c in matches]
        assert "user:123" in matched_ids
    
    def test_determine_merge_strategy(self):
        """Test determining merge strategy."""
        candidate1 = EntityCandidate(id="1", name="John", similarity=0.7, properties={"email": "john@example.com"})
        candidate2 = EntityCandidate(id="2", name="John Doe", similarity=0.8, properties={"email": "john@example.com", "phone": "123"})
        
        strategy = self.rules.determine_merge_strategy(candidate1, candidate2)
        
        # Should return PRESERVE_MOST_COMPLETE as default strategy
        assert strategy == MergeStrategy.PRESERVE_MOST_COMPLETE
    
    def test_resolve_property_conflict_preserves_longer_value(self):
        """Test property conflict resolution preserves longer value."""
        result = self.rules.resolve_property_conflict(
            "description", 
            "Short", 
            "This is a longer description", 
            "source1", 
            "source2"
        )
        
        assert result == "This is a longer description"
    
    def test_resolve_property_conflict_email_unchanged_if_equal(self):
        """Test email conflict resolution when values are equal."""
        result = self.rules.resolve_property_conflict(
            "email",
            "john@example.com", 
            "john@example.com",
            "source1",
            "source2"
        )
        
        assert result == "john@example.com"


class TestEntityDeduplicationEngine:
    """Test the entity deduplication engine."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.rules = DefaultEntityResolutionRules()
        self.engine = EntityDeduplicationEngine(self.rules)
    
    def test_find_duplicates_no_duplicates(self):
        """Test finding duplicates when there are none."""
        candidates = [
            EntityCandidate(id="1", name="John", similarity=0.8, properties={"email": "john1@example.com"}),
            EntityCandidate(id="2", name="Jane", similarity=0.7, properties={"email": "jane@example.com"}),
            EntityCandidate(id="3", name="Bob", similarity=0.6, properties={"email": "bob@example.com"})
        ]
        
        duplicates = self.engine.find_duplicates(candidates, threshold=0.9)
        
        assert len(duplicates) == 0
    
    def test_find_duplicates_with_duplicates(self):
        """Test finding duplicates when there are some."""
        candidates = [
            EntityCandidate(id="1", name="John Doe", similarity=0.9, properties={"email": "john@example.com", "role": "admin"}),
            EntityCandidate(id="2", name="John", similarity=0.85, properties={"email": "john@example.com", "role": "admin"}),
            EntityCandidate(id="3", name="Jane", similarity=0.7, properties={"email": "jane@example.com"})
        ]
        
        duplicates = self.engine.find_duplicates(candidates, threshold=0.7)
        
        # Should find the first two as duplicates (both have same email and similar name)
        assert len(duplicates) == 1
        assert len(duplicates[0]) == 2
        duplicate_ids = [c.id for c in duplicates[0]]
        assert "1" in duplicate_ids
        assert "2" in duplicate_ids
    
    def test_merge_entities_simple(self):
        """Test merging entities with simple properties."""
        candidates = [
            EntityCandidate(id="1", name="John Doe", similarity=0.9, properties={"email": "john@example.com", "role": "admin"}),
            EntityCandidate(id="2", name="John", similarity=0.8, properties={"email": "john@example.com", "phone": "123-456-7890"})
        ]
        
        merged = self.engine.merge_entities(candidates)
        
        # Should have combined properties
        assert merged.name == "John Doe"  # First name kept (more complete)
        assert "email" in merged.properties
        assert "role" in merged.properties
        assert "phone" in merged.properties
        assert merged.properties["email"] == "john@example.com"
        assert merged.properties["role"] == "admin"
        assert merged.properties["phone"] == "123-456-7890"
    
    def test_merge_entities_conflict_resolution(self):
        """Test merging entities with property conflicts."""
        candidates = [
            EntityCandidate(id="1", name="John Doe", similarity=0.8, properties={"description": "Software Engineer"}),
            EntityCandidate(id="2", name="John", similarity=0.9, properties={"description": "Senior Software Engineer with 5 years experience"})
        ]
        
        merged = self.engine.merge_entities(candidates)
        
        # Should keep the longer/complete description
        assert merged.properties["description"] == "Senior Software Engineer with 5 years experience"