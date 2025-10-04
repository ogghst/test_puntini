"""Tests for resolve_entities node implementation.

This module tests the resolve_entities node that implements Phase 2 of the
two-phase parsing architecture.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from langchain_core.messages import HumanMessage, AIMessage

from puntini.nodes.resolve_entities import resolve_entities
from puntini.models.intent_schemas import IntentSpec, ResolvedGoalSpec, ResolvedEntity, Ambiguity, IntentType
from puntini.models.goal_schemas import GoalComplexity
from puntini.models.errors import ValidationError


class TestResolveEntitiesNode:
    """Test cases for resolve_entities node."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_llm = Mock()
        self.mock_graph_store = Mock()
        self.mock_runtime = Mock()
        self.mock_runtime.context = {
            "llm": self.mock_llm,
            "graph_store": self.mock_graph_store
        }
        
        # Mock intent spec from Phase 1
        self.mock_intent_spec = IntentSpec(
            intent_type=IntentType.CREATE,
            mentioned_entities=["John", "Project Alpha"],
            requires_graph_context=True,
            complexity=GoalComplexity.MEDIUM,
            original_goal="Create a user John for Project Alpha"
        )
        
        # Mock parse goal response from Phase 1
        self.mock_parse_response = Mock()
        self.mock_parse_response.result.parsed_goal = self.mock_intent_spec.model_dump()
        
        self.valid_state = {
            "goal": "Create a user John for Project Alpha",
            "current_attempt": 1,
            "parse_goal_response": self.mock_parse_response
        }
    
    def test_resolve_entities_success(self):
        """Test successful entity resolution."""
        # Mock resolved entities
        mock_resolved_entity = ResolvedEntity(
            mention="John",
            entity_id="user:123",
            name="John Doe",
            entity_type="User",
            confidence=0.9,
            is_new=False,
            properties={"email": "john@example.com"}
        )
        
        # Mock resolved goal spec
        mock_resolved_goal = MagicMock(spec=ResolvedGoalSpec)
        mock_resolved_goal.entities = [mock_resolved_entity]
        mock_resolved_goal.ambiguities = []
        mock_resolved_goal.ready_to_execute = True
        mock_resolved_goal.has_ambiguities.return_value = False
        mock_resolved_goal.model_dump.return_value = {
            "intent_spec": self.mock_intent_spec.model_dump(),
            "entities": [mock_resolved_entity.model_dump()],
            "ambiguities": [],
            "ready_to_execute": True
        }
        
        self.mock_llm.with_structured_output.return_value.invoke.return_value = mock_resolved_goal
        
        # Ensure the mock's entities attribute is a list
        self.mock_llm.with_structured_output.return_value.invoke.return_value.entities = mock_resolved_goal.entities
        self.mock_llm.with_structured_output.return_value.invoke.return_value.ambiguities = mock_resolved_goal.ambiguities
        
        # Call the function
        result = resolve_entities(self.valid_state, runtime=self.mock_runtime)
        
        # Verify the result
        assert result.current_step == "plan_step"  # Should route to planning
        assert result.current_attempt == 1
        assert result.result.status == "success"
        assert result.result.parsed_goal["entities"][0]["mention"] == "John"
        assert result.result.parsed_goal["ready_to_execute"] is True
        assert result.result.requires_graph_ops is True
        assert result.result.is_simple is True
        
        # Verify LLM was called correctly
        self.mock_llm.with_structured_output.assert_called_once_with(ResolvedGoalSpec)
        self.mock_llm.with_structured_output.return_value.invoke.assert_called_once()
    
    def test_resolve_entities_with_ambiguities(self):
        """Test entity resolution with ambiguities."""
        # Mock resolved entities with ambiguity
        mock_resolved_entity = ResolvedEntity(
            mention="John",
            entity_id="user:123",
            name="John Doe",
            entity_type="User",
            confidence=0.9,
            is_new=False
        )
        
        # Mock ambiguity
        mock_ambiguity = Ambiguity(
            mention="Project",
            candidates=[
                {"id": "proj:123", "name": "Project Alpha", "confidence": 0.6},
                {"id": "proj:456", "name": "Project Beta", "confidence": 0.5}
            ],
            disambiguation_question="Which project?",
            context="Multiple projects found"
        )
        
        # Mock resolved goal spec with ambiguities
        mock_resolved_goal = MagicMock(spec=ResolvedGoalSpec)
        mock_resolved_goal.entities = [mock_resolved_entity]
        mock_resolved_goal.ambiguities = [mock_ambiguity]
        mock_resolved_goal.ready_to_execute = False
        mock_resolved_goal.has_ambiguities.return_value = True
        mock_resolved_goal.model_dump.return_value = {
            "intent_spec": self.mock_intent_spec.model_dump(),
            "entities": [mock_resolved_entity.model_dump()],
            "ambiguities": [mock_ambiguity.model_dump()],
            "ready_to_execute": False
        }
        
        self.mock_llm.with_structured_output.return_value.invoke.return_value = mock_resolved_goal
        
        # Ensure the mock's entities attribute is a list
        self.mock_llm.with_structured_output.return_value.invoke.return_value.entities = mock_resolved_goal.entities
        self.mock_llm.with_structured_output.return_value.invoke.return_value.ambiguities = mock_resolved_goal.ambiguities
        
        # Call the function
        result = resolve_entities(self.valid_state, runtime=self.mock_runtime)
        
        # Verify the result
        assert result.current_step == "disambiguate"  # Should route to disambiguation
        assert result.result.status == "success"
        assert result.result.parsed_goal["ready_to_execute"] is False
        assert len(result.result.parsed_goal["ambiguities"]) == 1
        assert result.result.is_simple is False
    
    def test_resolve_entities_no_parse_response(self):
        """Test handling when no parse response is found."""
        state_no_parse = {
            "goal": "Create a user John",
            "current_attempt": 1,
            "parse_goal_response": None
        }
        
        # Verify error handling
        with pytest.raises(ValidationError, match="No parsed intent found"):
            resolve_entities(state_no_parse, runtime=self.mock_runtime)
    
    def test_resolve_entities_invalid_parse_response(self):
        """Test handling when parse response is invalid."""
        # Mock invalid parse response
        mock_invalid_response = Mock()
        mock_invalid_response.result.parsed_goal = None
        
        state_invalid_parse = {
            "goal": "Create a user John",
            "current_attempt": 1,
            "parse_goal_response": mock_invalid_response
        }
        
        # Verify error handling
        with pytest.raises(ValidationError, match="No parsed intent data found"):
            resolve_entities(state_invalid_parse, runtime=self.mock_runtime)
    
    def test_resolve_entities_no_llm_in_context(self):
        """Test handling when LLM is not in runtime context."""
        # Mock runtime without LLM
        mock_runtime_no_llm = Mock()
        mock_runtime_no_llm.context = {"graph_store": self.mock_graph_store}
        
        result = resolve_entities(self.valid_state, runtime=mock_runtime_no_llm)
        
        # Verify error handling
        assert result.current_step == "escalate"
        assert result.result.status == "error"
        assert result.result.retryable is False
        assert "LLM not configured" in result.result.error
    
    def test_resolve_entities_no_graph_store(self):
        """Test handling when graph store is not in runtime context."""
        # Mock runtime without graph store
        mock_runtime_no_graph = Mock()
        mock_runtime_no_graph.context = {"llm": self.mock_llm}
        
        # Mock resolved goal spec
        mock_resolved_goal = MagicMock(spec=ResolvedGoalSpec)
        mock_resolved_goal.entities = []
        mock_resolved_goal.ambiguities = []
        mock_resolved_goal.ready_to_execute = True
        mock_resolved_goal.has_ambiguities.return_value = False
        mock_resolved_goal.model_dump.return_value = {
            "intent_spec": self.mock_intent_spec.model_dump(),
            "entities": [],
            "ambiguities": [],
            "ready_to_execute": True
        }
        
        self.mock_llm.with_structured_output.return_value.invoke.return_value = mock_resolved_goal
        
        # Ensure the mock's entities attribute is a list
        self.mock_llm.with_structured_output.return_value.invoke.return_value.entities = mock_resolved_goal.entities
        self.mock_llm.with_structured_output.return_value.invoke.return_value.ambiguities = mock_resolved_goal.ambiguities
        
        # Call the function
        result = resolve_entities(self.valid_state, runtime=mock_runtime_no_graph)
        
        # Verify it still works but with warning
        assert result.current_step == "plan_step"
        assert result.result.status == "success"
    
    def test_resolve_entities_llm_parsing_error(self):
        """Test handling of LLM parsing errors."""
        # Mock LLM to raise a JSON parsing error
        self.mock_llm.with_structured_output.return_value.invoke.side_effect = Exception("JSONDecodeError: Expecting value")
        
        result = resolve_entities(self.valid_state, runtime=self.mock_runtime)
        
        # Verify error handling
        assert result.current_step == "escalate"
        assert result.result.status == "error"
        assert result.result.retryable is False
        assert "LLM response was truncated" in result.result.error
    
    def test_resolve_entities_network_error_retryable(self):
        """Test handling of network errors that are retryable."""
        # Mock LLM to raise a network error
        self.mock_llm.with_structured_output.return_value.invoke.side_effect = Exception("Connection timeout")
        
        result = resolve_entities(self.valid_state, runtime=self.mock_runtime)
        
        # Verify error handling
        assert result.current_step == "diagnose"
        assert result.current_attempt == 2
        assert result.result.status == "error"
        assert result.result.retryable is True
        assert "network_error" in result.failures[0].error_type
    
    def test_resolve_entities_no_entities_resolved(self):
        """Test handling when no entities are resolved."""
        # Mock resolved goal spec with no entities
        mock_resolved_goal = MagicMock(spec=ResolvedGoalSpec)
        mock_resolved_goal.entities = []
        mock_resolved_goal.ambiguities = []
        mock_resolved_goal.ready_to_execute = False
        mock_resolved_goal.has_ambiguities.return_value = False
        mock_resolved_goal.model_dump.return_value = {
            "intent_spec": self.mock_intent_spec.model_dump(),
            "entities": [],
            "ambiguities": [],
            "ready_to_execute": False
        }
        
        self.mock_llm.with_structured_output.return_value.invoke.return_value = mock_resolved_goal
        
        # Ensure the mock's entities attribute is a list
        self.mock_llm.with_structured_output.return_value.invoke.return_value.entities = mock_resolved_goal.entities
        self.mock_llm.with_structured_output.return_value.invoke.return_value.ambiguities = mock_resolved_goal.ambiguities
        
        result = resolve_entities(self.valid_state, runtime=self.mock_runtime)
        
        # Verify error handling
        assert result.current_step == "escalate"
        assert result.result.status == "error"
        assert result.result.retryable is False
        assert "Could not resolve any entities" in result.result.error
    
    def test_resolve_entities_routing_logic(self):
        """Test the routing logic for different resolution results."""
        test_cases = [
            # (has_ambiguities, ready_to_execute, expected_route)
            (False, True, "plan_step"),
            (True, False, "disambiguate"),
            (False, False, "plan_step"),
        ]
        
        for has_ambiguities, ready_to_execute, expected_route in test_cases:
            # Mock resolved goal spec
            mock_resolved_goal = MagicMock(spec=ResolvedGoalSpec)
            mock_resolved_goal.entities = []
            mock_resolved_goal.ambiguities = [Mock()] if has_ambiguities else []
            mock_resolved_goal.ready_to_execute = ready_to_execute
            mock_resolved_goal.has_ambiguities.return_value = has_ambiguities
            mock_resolved_goal.model_dump.return_value = {
                "intent_spec": self.mock_intent_spec.model_dump(),
                "entities": [],
                "ambiguities": [Mock()] if has_ambiguities else [],
                "ready_to_execute": ready_to_execute
            }
            
            self.mock_llm.with_structured_output.return_value.invoke.return_value = mock_resolved_goal
            
            # Call the function
            result = resolve_entities(self.valid_state, runtime=self.mock_runtime)
            
            # Verify routing
            assert result.current_step == expected_route, f"Failed for has_ambiguities={has_ambiguities}, ready_to_execute={ready_to_execute}"
    
    def test_resolve_entities_progress_tracking(self):
        """Test that progress is properly tracked."""
        # Mock resolved goal spec
        mock_resolved_entity = ResolvedEntity(
            mention="John",
            name="John Doe",
            entity_type="User",
            confidence=0.9,
            is_new=False
        )
        
        mock_resolved_goal = MagicMock(spec=ResolvedGoalSpec)
        mock_resolved_goal.entities = [mock_resolved_entity]
        mock_resolved_goal.ambiguities = []
        mock_resolved_goal.ready_to_execute = True
        mock_resolved_goal.has_ambiguities.return_value = False
        mock_resolved_goal.model_dump.return_value = {
            "intent_spec": self.mock_intent_spec.model_dump(),
            "entities": [mock_resolved_entity.model_dump()],
            "ambiguities": [],
            "ready_to_execute": True
        }
        
        self.mock_llm.with_structured_output.return_value.invoke.return_value = mock_resolved_goal
        
        # Ensure the mock's entities attribute is a list
        self.mock_llm.with_structured_output.return_value.invoke.return_value.entities = mock_resolved_goal.entities
        self.mock_llm.with_structured_output.return_value.invoke.return_value.ambiguities = mock_resolved_goal.ambiguities
        
        # Call the function
        result = resolve_entities(self.valid_state, runtime=self.mock_runtime)
        
        # Verify progress tracking
        assert len(result.progress) == 1
        assert "Resolved 1 entities" in result.progress[0]
    
    def test_resolve_entities_artifacts_and_failures(self):
        """Test that artifacts and failures are properly handled."""
        # Mock resolved goal spec
        mock_resolved_goal = MagicMock(spec=ResolvedGoalSpec)
        mock_resolved_goal.entities = []
        mock_resolved_goal.ambiguities = []
        mock_resolved_goal.ready_to_execute = True
        mock_resolved_goal.has_ambiguities.return_value = False
        mock_resolved_goal.model_dump.return_value = {
            "intent_spec": self.mock_intent_spec.model_dump(),
            "entities": [],
            "ambiguities": [],
            "ready_to_execute": True
        }
        
        self.mock_llm.with_structured_output.return_value.invoke.return_value = mock_resolved_goal
        
        # Ensure the mock's entities attribute is a list
        self.mock_llm.with_structured_output.return_value.invoke.return_value.entities = mock_resolved_goal.entities
        self.mock_llm.with_structured_output.return_value.invoke.return_value.ambiguities = mock_resolved_goal.ambiguities
        
        # Call the function
        result = resolve_entities(self.valid_state, runtime=self.mock_runtime)
        
        # Verify artifacts and failures
        assert result.artifacts == []  # No artifacts for entity resolution
        assert result.failures == []  # No failures for successful resolution
