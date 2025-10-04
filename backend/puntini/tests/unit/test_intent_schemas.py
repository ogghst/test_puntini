"""Tests for intent parsing schemas.

This module tests the Pydantic models for the two-phase parsing architecture,
including IntentSpec, ResolvedEntity, Ambiguity, and ResolvedGoalSpec.
"""

import pytest
from pydantic import ValidationError

from puntini.models.intent_schemas import (
    IntentSpec, IntentType, ResolvedEntity, Ambiguity, ResolvedGoalSpec
)
from puntini.models.goal_schemas import GoalComplexity


class TestIntentSpec:
    """Test cases for IntentSpec model."""
    
    def test_valid_intent_spec(self):
        """Test creating a valid IntentSpec."""
        intent = IntentSpec(
            intent_type=IntentType.CREATE,
            mentioned_entities=["John", "Project Alpha"],
            requires_graph_context=True,
            complexity=GoalComplexity.MEDIUM,
            original_goal="Create a user John for Project Alpha"
        )
        
        assert intent.intent_type == IntentType.CREATE
        assert intent.mentioned_entities == ["John", "Project Alpha"]
        assert intent.requires_graph_context is True
        assert intent.complexity == GoalComplexity.MEDIUM
        assert intent.original_goal == "Create a user John for Project Alpha"
    
    def test_is_simple_intent(self):
        """Test the is_simple_intent method."""
        # Simple intent
        simple_intent = IntentSpec(
            intent_type=IntentType.QUERY,
            mentioned_entities=["users"],
            requires_graph_context=False,
            complexity=GoalComplexity.SIMPLE,
            original_goal="Show me all users"
        )
        assert simple_intent.is_simple_intent() is True
        
        # Complex intent
        complex_intent = IntentSpec(
            intent_type=IntentType.CREATE,
            mentioned_entities=["John", "Project Alpha", "Task Beta"],
            requires_graph_context=True,
            complexity=GoalComplexity.COMPLEX,
            original_goal="Create a user John for Project Alpha with Task Beta"
        )
        assert complex_intent.is_simple_intent() is False
        
        # Medium complexity with graph context
        medium_intent = IntentSpec(
            intent_type=IntentType.UPDATE,
            mentioned_entities=["John"],
            requires_graph_context=True,
            complexity=GoalComplexity.MEDIUM,
            original_goal="Update user John"
        )
        assert medium_intent.is_simple_intent() is False


class TestResolvedEntity:
    """Test cases for ResolvedEntity model."""
    
    def test_valid_resolved_entity(self):
        """Test creating a valid ResolvedEntity."""
        entity = ResolvedEntity(
            mention="John",
            entity_id="user:123",
            name="John Doe",
            entity_type="User",
            confidence=0.95,
            is_new=False,
            properties={"email": "john@example.com", "role": "admin"}
        )
        
        assert entity.mention == "John"
        assert entity.entity_id == "user:123"
        assert entity.name == "John Doe"
        assert entity.entity_type == "User"
        assert entity.confidence == 0.95
        assert entity.is_new is False
        assert entity.properties == {"email": "john@example.com", "role": "admin"}
    
    def test_is_ambiguous(self):
        """Test the is_ambiguous method."""
        # High confidence - not ambiguous
        high_confidence = ResolvedEntity(
            mention="John",
            name="John Doe",
            entity_type="User",
            confidence=0.95,
            is_new=False
        )
        assert high_confidence.is_ambiguous() is False
        
        # Low confidence - not ambiguous (too low)
        low_confidence = ResolvedEntity(
            mention="John",
            name="John Doe",
            entity_type="User",
            confidence=0.2,
            is_new=False
        )
        assert low_confidence.is_ambiguous() is False
        
        # Medium confidence - ambiguous
        medium_confidence = ResolvedEntity(
            mention="John",
            name="John Doe",
            entity_type="User",
            confidence=0.5,
            is_new=False
        )
        assert medium_confidence.is_ambiguous() is True
    
    def test_confidence_validation(self):
        """Test confidence score validation."""
        # Valid confidence scores
        ResolvedEntity(
            mention="John",
            name="John Doe",
            entity_type="User",
            confidence=0.0,
            is_new=False
        )
        ResolvedEntity(
            mention="John",
            name="John Doe",
            entity_type="User",
            confidence=1.0,
            is_new=False
        )
        
        # Invalid confidence scores
        with pytest.raises(ValidationError):
            ResolvedEntity(
                mention="John",
                name="John Doe",
                entity_type="User",
                confidence=-0.1,
                is_new=False
            )
        
        with pytest.raises(ValidationError):
            ResolvedEntity(
                mention="John",
                name="John Doe",
                entity_type="User",
                confidence=1.1,
                is_new=False
            )


class TestAmbiguity:
    """Test cases for Ambiguity model."""
    
    def test_valid_ambiguity(self):
        """Test creating a valid Ambiguity."""
        ambiguity = Ambiguity(
            mention="John",
            candidates=[
                {"id": "user:123", "name": "John Doe", "confidence": 0.8},
                {"id": "user:456", "name": "John Smith", "confidence": 0.7}
            ],
            disambiguation_question="Which John do you mean?",
            context="There are multiple users named John in the system"
        )
        
        assert ambiguity.mention == "John"
        assert len(ambiguity.candidates) == 2
        assert ambiguity.disambiguation_question == "Which John do you mean?"
        assert ambiguity.context == "There are multiple users named John in the system"


class TestResolvedGoalSpec:
    """Test cases for ResolvedGoalSpec model."""
    
    def test_valid_resolved_goal_spec(self):
        """Test creating a valid ResolvedGoalSpec."""
        intent_spec = IntentSpec(
            intent_type=IntentType.CREATE,
            mentioned_entities=["John"],
            requires_graph_context=True,
            complexity=GoalComplexity.SIMPLE,
            original_goal="Create user John"
        )
        
        resolved_entity = ResolvedEntity(
            mention="John",
            name="John Doe",
            entity_type="User",
            confidence=0.9,
            is_new=True
        )
        
        ambiguity = Ambiguity(
            mention="Project",
            candidates=[
                {"id": "proj:123", "name": "Project Alpha", "confidence": 0.6},
                {"id": "proj:456", "name": "Project Beta", "confidence": 0.5}
            ],
            disambiguation_question="Which project?",
            context="Multiple projects found"
        )
        
        resolved_goal = ResolvedGoalSpec(
            intent_spec=intent_spec,
            entities=[resolved_entity],
            ambiguities=[ambiguity],
            ready_to_execute=False
        )
        
        assert resolved_goal.intent_spec == intent_spec
        assert len(resolved_goal.entities) == 1
        assert len(resolved_goal.ambiguities) == 1
        assert resolved_goal.ready_to_execute is False
    
    def test_has_ambiguities(self):
        """Test the has_ambiguities method."""
        intent_spec = IntentSpec(
            intent_type=IntentType.QUERY,
            mentioned_entities=["users"],
            requires_graph_context=False,
            complexity=GoalComplexity.SIMPLE,
            original_goal="Show users"
        )
        
        # No ambiguities
        resolved_goal_no_ambiguities = ResolvedGoalSpec(
            intent_spec=intent_spec,
            entities=[],
            ambiguities=[],
            ready_to_execute=True
        )
        assert resolved_goal_no_ambiguities.has_ambiguities() is False
        
        # With ambiguities
        ambiguity = Ambiguity(
            mention="John",
            candidates=[],
            disambiguation_question="Which John?",
            context="Multiple Johns found"
        )
        
        resolved_goal_with_ambiguities = ResolvedGoalSpec(
            intent_spec=intent_spec,
            entities=[],
            ambiguities=[ambiguity],
            ready_to_execute=False
        )
        assert resolved_goal_with_ambiguities.has_ambiguities() is True
    
    def test_get_ambiguous_entities(self):
        """Test the get_ambiguous_entities method."""
        intent_spec = IntentSpec(
            intent_type=IntentType.CREATE,
            mentioned_entities=["John", "Project"],
            requires_graph_context=True,
            complexity=GoalComplexity.MEDIUM,
            original_goal="Create user John for Project"
        )
        
        # High confidence entity
        high_confidence_entity = ResolvedEntity(
            mention="John",
            name="John Doe",
            entity_type="User",
            confidence=0.9,
            is_new=True
        )
        
        # Ambiguous entity
        ambiguous_entity = ResolvedEntity(
            mention="Project",
            name="Project Alpha",
            entity_type="Project",
            confidence=0.5,
            is_new=False
        )
        
        resolved_goal = ResolvedGoalSpec(
            intent_spec=intent_spec,
            entities=[high_confidence_entity, ambiguous_entity],
            ambiguities=[],
            ready_to_execute=False
        )
        
        ambiguous_entities = resolved_goal.get_ambiguous_entities()
        assert len(ambiguous_entities) == 1
        assert ambiguous_entities[0] == ambiguous_entity
    
    def test_get_high_confidence_entities(self):
        """Test the get_high_confidence_entities method."""
        intent_spec = IntentSpec(
            intent_type=IntentType.CREATE,
            mentioned_entities=["John", "Project"],
            requires_graph_context=True,
            complexity=GoalComplexity.MEDIUM,
            original_goal="Create user John for Project"
        )
        
        # High confidence entity
        high_confidence_entity = ResolvedEntity(
            mention="John",
            name="John Doe",
            entity_type="User",
            confidence=0.9,
            is_new=True
        )
        
        # Low confidence entity
        low_confidence_entity = ResolvedEntity(
            mention="Project",
            name="Project Alpha",
            entity_type="Project",
            confidence=0.2,
            is_new=False
        )
        
        # Medium confidence entity
        medium_confidence_entity = ResolvedEntity(
            mention="Task",
            name="Task Beta",
            entity_type="Task",
            confidence=0.5,
            is_new=True
        )
        
        resolved_goal = ResolvedGoalSpec(
            intent_spec=intent_spec,
            entities=[high_confidence_entity, low_confidence_entity, medium_confidence_entity],
            ambiguities=[],
            ready_to_execute=False
        )
        
        high_confidence_entities = resolved_goal.get_high_confidence_entities()
        assert len(high_confidence_entities) == 1
        assert high_confidence_entities[0] == high_confidence_entity
