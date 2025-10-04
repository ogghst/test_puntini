"""Tests for entity resolution models."""

import sys
sys.path.append('/home/nicola/dev/puntini/backend')

import pytest
from uuid import UUID, uuid4
from datetime import datetime
from typing import Dict, Any

from puntini.entity_resolution.models import (
    GraphElementType,
    ResolutionStrategy,
    ResolutionStatus,
    EntityConfidence,
    EntityMention,
    EntityCandidate,
    EntityResolution,
    AmbiguityResolution
)


class TestGraphElementType:
    """Test GraphElementType enum."""
    
    def test_enum_values(self):
        """Test that enum has expected values."""
        assert GraphElementType.NODE_REFERENCE == "node_ref"
        assert GraphElementType.EDGE_REFERENCE == "edge_ref"
        assert GraphElementType.LITERAL_VALUE == "literal"
        assert GraphElementType.SCHEMA_REFERENCE == "schema_ref"
    
    def test_enum_membership(self):
        """Test enum membership."""
        assert "node_ref" in GraphElementType.__members__.values()
        assert "edge_ref" in GraphElementType.__members__.values()
        assert "literal" in GraphElementType.__members__.values()
        assert "schema_ref" in GraphElementType.__members__.values()


class TestEntityConfidence:
    """Test EntityConfidence model."""
    
    def test_valid_confidence(self):
        """Test creating valid confidence score."""
        confidence = EntityConfidence(
            name_match=0.8,
            type_match=0.9,
            property_match=0.7,
            context_match=0.6,
            overall=0.75
        )
        assert confidence.name_match == 0.8
        assert confidence.type_match == 0.9
        assert confidence.property_match == 0.7
        assert confidence.context_match == 0.6
        assert confidence.overall == 0.75
    
    def test_confidence_bounds(self):
        """Test confidence bounds validation."""
        # Valid bounds
        confidence = EntityConfidence(
            name_match=0.0,
            type_match=1.0,
            property_match=0.5,
            context_match=0.3,
            overall=0.4
        )
        assert confidence.name_match == 0.0
        assert confidence.type_match == 1.0
        
        # Invalid bounds should raise ValueError
        with pytest.raises(ValueError):
            EntityConfidence(
                name_match=-0.1,
                type_match=0.5,
                property_match=0.5,
                context_match=0.5,
                overall=0.5
            )
        
        with pytest.raises(ValueError):
            EntityConfidence(
                name_match=1.1,
                type_match=0.5,
                property_match=0.5,
                context_match=0.5,
                overall=0.5
            )
    
    def test_is_certain(self):
        """Test is_certain method."""
        high_confidence = EntityConfidence(
            name_match=0.9,
            type_match=0.9,
            property_match=0.9,
            context_match=0.9,
            overall=0.96
        )
        assert high_confidence.is_certain() is True
        
        low_confidence = EntityConfidence(
            name_match=0.5,
            type_match=0.5,
            property_match=0.5,
            context_match=0.5,
            overall=0.5
        )
        assert low_confidence.is_certain() is False
    
    def test_requires_human(self):
        """Test requires_human method."""
        medium_confidence = EntityConfidence(
            name_match=0.6,
            type_match=0.6,
            property_match=0.6,
            context_match=0.6,
            overall=0.6
        )
        assert medium_confidence.requires_human() is True
        
        high_confidence = EntityConfidence(
            name_match=0.8,
            type_match=0.8,
            property_match=0.8,
            context_match=0.8,
            overall=0.8
        )
        assert high_confidence.requires_human() is False
        
        low_confidence = EntityConfidence(
            name_match=0.2,
            type_match=0.2,
            property_match=0.2,
            context_match=0.2,
            overall=0.2
        )
        assert low_confidence.requires_human() is False
    
    def test_is_too_low(self):
        """Test is_too_low method."""
        low_confidence = EntityConfidence(
            name_match=0.2,
            type_match=0.2,
            property_match=0.2,
            context_match=0.2,
            overall=0.2
        )
        assert low_confidence.is_too_low() is True
        
        medium_confidence = EntityConfidence(
            name_match=0.5,
            type_match=0.5,
            property_match=0.5,
            context_match=0.5,
            overall=0.5
        )
        assert medium_confidence.is_too_low() is False


class TestEntityMention:
    """Test EntityMention model."""
    
    def test_create_mention(self):
        """Test creating entity mention."""
        mention = EntityMention(
            surface_form="John Doe",
            element_type=GraphElementType.NODE_REFERENCE
        )
        assert mention.surface_form == "John Doe"
        assert mention.element_type == GraphElementType.NODE_REFERENCE
        assert mention.canonical_id is None
        assert isinstance(mention.id, UUID)
        assert isinstance(mention.created_at, datetime)
    
    def test_surface_form_validation(self):
        """Test surface form validation."""
        # Valid surface form
        mention = EntityMention(
            surface_form="John Doe",
            element_type=GraphElementType.NODE_REFERENCE
        )
        assert mention.surface_form == "John Doe"
        
        # Empty surface form should raise error
        with pytest.raises(ValueError):
            EntityMention(
                surface_form="",
                element_type=GraphElementType.NODE_REFERENCE
            )
        
        with pytest.raises(ValueError):
            EntityMention(
                surface_form="   ",
                element_type=GraphElementType.NODE_REFERENCE
            )
    
    def test_surface_form_normalization(self):
        """Test surface form normalization."""
        mention = EntityMention(
            surface_form="  John Doe  ",
            element_type=GraphElementType.NODE_REFERENCE
        )
        assert mention.surface_form == "John Doe"


class TestEntityCandidate:
    """Test EntityCandidate model."""
    
    def test_create_candidate(self):
        """Test creating entity candidate."""
        candidate = EntityCandidate(
            id="user:123",
            name="John Doe",
            similarity=0.8
        )
        assert candidate.id == "user:123"
        assert candidate.name == "John Doe"
        assert candidate.similarity == 0.8
        assert candidate.label is None
        assert candidate.properties == {}
        assert candidate.context == {}
    
    def test_name_validation(self):
        """Test name validation."""
        # Valid name
        candidate = EntityCandidate(
            id="user:123",
            name="John Doe",
            similarity=0.8
        )
        assert candidate.name == "John Doe"
        
        # Empty name should raise error
        with pytest.raises(ValueError):
            EntityCandidate(
                id="user:123",
                name="",
                similarity=0.8
            )
        
        with pytest.raises(ValueError):
            EntityCandidate(
                id="user:123",
                name="   ",
                similarity=0.8
            )
    
    def test_similarity_bounds(self):
        """Test similarity bounds validation."""
        # Valid bounds
        candidate = EntityCandidate(
            id="user:123",
            name="John Doe",
            similarity=0.0
        )
        assert candidate.similarity == 0.0
        
        candidate = EntityCandidate(
            id="user:123",
            name="John Doe",
            similarity=1.0
        )
        assert candidate.similarity == 1.0
        
        # Invalid bounds should raise ValueError
        with pytest.raises(ValueError):
            EntityCandidate(
                id="user:123",
                name="John Doe",
                similarity=-0.1
            )
        
        with pytest.raises(ValueError):
            EntityCandidate(
                id="user:123",
                name="John Doe",
                similarity=1.1
            )


class TestEntityResolution:
    """Test EntityResolution model."""
    
    def test_create_resolution(self):
        """Test creating entity resolution."""
        confidence = EntityConfidence(
            name_match=0.8,
            type_match=0.9,
            property_match=0.7,
            context_match=0.6,
            overall=0.75
        )
        
        resolution = EntityResolution(
            mention_id=uuid4(),
            strategy=ResolutionStrategy.USE_EXISTING,
            entity_id="user:123",
            confidence=confidence,
            reasoning="High confidence match found"
        )
        
        assert resolution.strategy == ResolutionStrategy.USE_EXISTING
        assert resolution.entity_id == "user:123"
        assert resolution.confidence == confidence
        assert resolution.reasoning == "High confidence match found"
        assert isinstance(resolution.mention_id, UUID)
        assert isinstance(resolution.created_at, datetime)
    
    def test_validation_use_existing_requires_entity_id(self):
        """Test that USE_EXISTING strategy requires entity_id."""
        confidence = EntityConfidence(
            name_match=0.8,
            type_match=0.9,
            property_match=0.7,
            context_match=0.6,
            overall=0.75
        )
        
        # Should raise error if entity_id is None for USE_EXISTING
        with pytest.raises(ValueError):
            EntityResolution(
                strategy=ResolutionStrategy.USE_EXISTING,
                entity_id=None,
                confidence=confidence,
                reasoning="High confidence match found"
            )
    
    def test_validation_create_new_should_not_have_entity_id(self):
        """Test that CREATE_NEW strategy should not have entity_id."""
        confidence = EntityConfidence(
            name_match=0.8,
            type_match=0.9,
            property_match=0.7,
            context_match=0.6,
            overall=0.75
        )
        
        # Should raise error if entity_id is set for CREATE_NEW
        with pytest.raises(ValueError):
            EntityResolution(
                strategy=ResolutionStrategy.CREATE_NEW,
                entity_id="user:123",
                confidence=confidence,
                reasoning="Creating new entity"
            )


class TestAmbiguityResolution:
    """Test AmbiguityResolution model."""
    
    def test_create_ambiguity(self):
        """Test creating ambiguity resolution."""
        mention = EntityMention(
            surface_form="John",
            element_type=GraphElementType.NODE_REFERENCE
        )
        
        candidate1 = EntityCandidate(
            id="user:123",
            name="John Doe",
            similarity=0.8
        )
        
        candidate2 = EntityCandidate(
            id="user:456",
            name="John Smith",
            similarity=0.7
        )
        
        ambiguity = AmbiguityResolution(
            ambiguous_entities=[mention],
            disambiguation_question="Which John did you mean?",
            candidates_per_entity={
                "John": [candidate1, candidate2]
            }
        )
        
        assert len(ambiguity.ambiguous_entities) == 1
        assert ambiguity.disambiguation_question == "Which John did you mean?"
        assert len(ambiguity.candidates_per_entity["John"]) == 2
        assert ambiguity.resolution_status == ResolutionStatus.PENDING
        assert ambiguity.user_response is None
        assert isinstance(ambiguity.id, UUID)
        assert isinstance(ambiguity.created_at, datetime)
        assert ambiguity.resolved_at is None
    
    def test_disambiguation_question_validation(self):
        """Test disambiguation question validation."""
        mention = EntityMention(
            surface_form="John",
            element_type=GraphElementType.NODE_REFERENCE
        )
        
        # Valid question
        ambiguity = AmbiguityResolution(
            ambiguous_entities=[mention],
            disambiguation_question="Which John did you mean?",
            candidates_per_entity={"John": []}
        )
        assert ambiguity.disambiguation_question == "Which John did you mean?"
        
        # Empty question should raise error
        with pytest.raises(ValueError):
            AmbiguityResolution(
                ambiguous_entities=[mention],
                disambiguation_question="",
                candidates_per_entity={"John": []}
            )
        
        with pytest.raises(ValueError):
            AmbiguityResolution(
                ambiguous_entities=[mention],
                disambiguation_question="   ",
                candidates_per_entity={"John": []}
            )
    
    def test_is_resolved(self):
        """Test is_resolved method."""
        mention = EntityMention(
            surface_form="John",
            element_type=GraphElementType.NODE_REFERENCE
        )
        
        # Pending resolution
        ambiguity = AmbiguityResolution(
            ambiguous_entities=[mention],
            disambiguation_question="Which John did you mean?",
            candidates_per_entity={"John": []}
        )
        assert ambiguity.is_resolved() is False
        
        # Resolved
        ambiguity.resolution_status = ResolutionStatus.RESOLVED
        assert ambiguity.is_resolved() is True
    
    def test_is_pending(self):
        """Test is_pending method."""
        mention = EntityMention(
            surface_form="John",
            element_type=GraphElementType.NODE_REFERENCE
        )
        
        # Pending resolution
        ambiguity = AmbiguityResolution(
            ambiguous_entities=[mention],
            disambiguation_question="Which John did you mean?",
            candidates_per_entity={"John": []}
        )
        assert ambiguity.is_pending() is True
        
        # Resolved
        ambiguity.resolution_status = ResolutionStatus.RESOLVED
        assert ambiguity.is_pending() is False

