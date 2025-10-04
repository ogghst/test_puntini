"""Tests for disambiguate node implementation.

This module tests the disambiguate node that handles ambiguous entity
references with user interaction.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from langchain_core.messages import HumanMessage, AIMessage

from puntini.nodes.disambiguate import disambiguate
from puntini.models.intent_schemas import IntentSpec, ResolvedGoalSpec, ResolvedEntity, Ambiguity, IntentType
from puntini.models.goal_schemas import GoalComplexity
from puntini.models.errors import ValidationError


class TestDisambiguateNode:
    """Test cases for disambiguate node."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_llm = Mock()
        self.mock_runtime = Mock()
        self.mock_runtime.context = {"llm": self.mock_llm}
        
        # Mock intent spec from Phase 1
        self.mock_intent_spec = IntentSpec(
            intent_type=IntentType.CREATE,
            mentioned_entities=["John", "Project"],
            requires_graph_context=True,
            complexity=GoalComplexity.MEDIUM,
            original_goal="Create a user John for Project"
        )
        
        # Mock resolved entity
        self.mock_resolved_entity = ResolvedEntity(
            mention="John",
            entity_id="user:123",
            name="John Doe",
            entity_type="User",
            confidence=0.9,
            is_new=False
        )
        
        # Mock ambiguity
        self.mock_ambiguity = Ambiguity(
            mention="Project",
            candidates=[
                {"id": "proj:123", "name": "Project Alpha", "confidence": 0.6},
                {"id": "proj:456", "name": "Project Beta", "confidence": 0.5}
            ],
            disambiguation_question="Which project?",
            context="Multiple projects found"
        )
        
        # Mock resolved goal spec with ambiguities
        self.mock_resolved_goal = ResolvedGoalSpec(
            intent_spec=self.mock_intent_spec,
            entities=[self.mock_resolved_entity],
            ambiguities=[self.mock_ambiguity],
            ready_to_execute=False
        )
        
        # Mock parse goal response from Phase 2
        self.mock_parse_response = Mock()
        self.mock_parse_response.result.parsed_goal = self.mock_resolved_goal.model_dump()
        
        self.valid_state = {
            "goal": "Create a user John for Project",
            "current_attempt": 1,
            "parse_goal_response": self.mock_parse_response
        }
    
    def test_disambiguate_success(self):
        """Test successful disambiguation."""
        # Mock LLM response for disambiguation questions
        mock_llm_response = Mock()
        mock_llm_response.content = "Which project do you mean: Project Alpha or Project Beta?"
        self.mock_llm.invoke.return_value = mock_llm_response
        
        # Call the function
        result = disambiguate(self.valid_state, runtime=self.mock_runtime)
        
        # Verify the result
        assert result.current_step == "plan_step"  # Will be updated when resumed
        assert result.current_attempt == 1
        assert result.result.status == "success"
        assert result.result.parsed_goal["ambiguities"][0]["mention"] == "Project"
        assert result.result.requires_graph_ops is True
        assert result.result.is_simple is False
        
        # Verify LLM was called for generating disambiguation questions
        self.mock_llm.invoke.assert_called_once()
    
    def test_disambiguate_no_ambiguities(self):
        """Test handling when there are no ambiguities."""
        # Mock resolved goal spec without ambiguities
        mock_resolved_goal_no_ambiguities = ResolvedGoalSpec(
            intent_spec=self.mock_intent_spec,
            entities=[self.mock_resolved_entity],
            ambiguities=[],  # No ambiguities
            ready_to_execute=True
        )
        
        # Mock parse goal response
        mock_parse_response = Mock()
        mock_parse_response.result.parsed_goal = mock_resolved_goal_no_ambiguities.model_dump()
        
        state_no_ambiguities = {
            "goal": "Create a user John",
            "current_attempt": 1,
            "parse_goal_response": mock_parse_response
        }
        
        result = disambiguate(state_no_ambiguities, runtime=self.mock_runtime)
        
        # Verify routing to planning
        assert result.current_step == "plan_step"
        assert result.result.status == "success"
        assert "No ambiguities found" in result.progress[0]
    
    def test_disambiguate_no_parse_response(self):
        """Test handling when no parse response is found."""
        state_no_parse = {
            "goal": "Create a user John",
            "current_attempt": 1,
            "parse_goal_response": None
        }
        
        result = disambiguate(state_no_parse, runtime=self.mock_runtime)
        
        # Verify error handling
        assert result.current_step == "escalate"
        assert result.result.status == "error"
        assert result.result.retryable is False
        assert "No resolved goal found" in result.result.error
    
    def test_disambiguate_invalid_parse_response(self):
        """Test handling when parse response is invalid."""
        # Mock invalid parse response
        mock_invalid_response = Mock()
        mock_invalid_response.result.parsed_goal = None
        
        state_invalid_parse = {
            "goal": "Create a user John",
            "current_attempt": 1,
            "parse_goal_response": mock_invalid_response
        }
        
        result = disambiguate(state_invalid_parse, runtime=self.mock_runtime)
        
        # Verify error handling
        assert result.current_step == "escalate"
        assert result.result.status == "error"
        assert result.result.retryable is False
        assert "No resolved goal data found" in result.result.error
    
    def test_disambiguate_no_llm_in_context(self):
        """Test handling when LLM is not in runtime context."""
        # Mock runtime without LLM
        mock_runtime_no_llm = Mock()
        mock_runtime_no_llm.context = {}
        
        result = disambiguate(self.valid_state, runtime=mock_runtime_no_llm)
        
        # Verify error handling
        assert result.current_step == "escalate"
        assert result.result.status == "error"
        assert result.result.retryable is False
        assert "LLM not configured" in result.result.error
    
    def test_disambiguate_llm_generation_error(self):
        """Test handling when LLM fails to generate disambiguation questions."""
        # Mock LLM to raise an error
        self.mock_llm.invoke.side_effect = Exception("LLM generation failed")
        
        result = disambiguate(self.valid_state, runtime=self.mock_runtime)
        
        # Verify it still works with fallback message
        assert result.current_step == "plan_step"
        assert result.result.status == "success"
        assert "Waiting for user disambiguation input" in result.progress[0]
    
    def test_disambiguate_validation_error(self):
        """Test handling of validation errors."""
        # Test with invalid state
        invalid_state = {
            "goal": "",  # Empty goal
            "current_attempt": 1,
            "parse_goal_response": self.mock_parse_response
        }
        
        result = disambiguate(invalid_state, runtime=self.mock_runtime)
        
        # Verify error handling
        assert result.current_step == "escalate"
        assert result.result.status == "error"
        assert result.result.retryable is False
        assert "Goal must be a string" in result.result.error
    
    def test_disambiguate_network_error_retryable(self):
        """Test handling of network errors that are retryable."""
        # Mock LLM to raise a network error
        self.mock_llm.invoke.side_effect = Exception("Connection timeout")
        
        result = disambiguate(self.valid_state, runtime=self.mock_runtime)
        
        # Verify error handling
        assert result.current_step == "diagnose"
        assert result.current_attempt == 2
        assert result.result.status == "error"
        assert result.result.retryable is True
        assert "network_error" in result.failures[0].error_type
    
    def test_disambiguate_multiple_attempts_failure(self):
        """Test handling when multiple attempts fail."""
        # Mock LLM to raise a network error
        self.mock_llm.invoke.side_effect = Exception("Connection timeout")
        
        # Test with current_attempt > 1
        state_with_retry = {
            "goal": "Create a user John",
            "current_attempt": 2,
            "parse_goal_response": self.mock_parse_response
        }
        
        result = disambiguate(state_with_retry, runtime=self.mock_runtime)
        
        # Verify error handling
        assert result.current_step == "escalate"
        assert result.current_attempt == 2
        assert result.result.status == "error"
        assert result.result.retryable is True
    
    def test_disambiguate_progress_tracking(self):
        """Test that progress is properly tracked."""
        # Mock LLM response
        mock_llm_response = Mock()
        mock_llm_response.content = "Which project?"
        self.mock_llm.invoke.return_value = mock_llm_response
        
        # Call the function
        result = disambiguate(self.valid_state, runtime=self.mock_runtime)
        
        # Verify progress tracking
        assert len(result.progress) == 1
        assert "Waiting for user disambiguation input" in result.progress[0]
    
    def test_disambiguate_artifacts_and_failures(self):
        """Test that artifacts and failures are properly handled."""
        # Mock LLM response
        mock_llm_response = Mock()
        mock_llm_response.content = "Which project?"
        self.mock_llm.invoke.return_value = mock_llm_response
        
        # Call the function
        result = disambiguate(self.valid_state, runtime=self.mock_runtime)
        
        # Verify artifacts and failures
        assert result.artifacts == []  # No artifacts for disambiguation
        assert result.failures == []  # No failures for successful disambiguation
    
    def test_disambiguate_interrupt_mechanism(self):
        """Test that the interrupt mechanism is properly set up."""
        # Mock LLM response
        mock_llm_response = Mock()
        mock_llm_response.content = "Which project?"
        self.mock_llm.invoke.return_value = mock_llm_response
        
        # Call the function
        result = disambiguate(self.valid_state, runtime=self.mock_runtime)
        
        # Verify the result indicates waiting for user input
        assert result.current_step == "plan_step"  # Will be updated when resumed
        assert result.result.status == "success"
        assert "Waiting for user disambiguation input" in result.progress[0]
        
        # Note: The actual interrupt() call is tested in integration tests
        # since it requires the full LangGraph runtime
    
    def test_disambiguate_fallback_message_generation(self):
        """Test fallback disambiguation message generation."""
        # Mock LLM to raise an error
        self.mock_llm.invoke.side_effect = Exception("LLM generation failed")
        
        # Call the function
        result = disambiguate(self.valid_state, runtime=self.mock_runtime)
        
        # Verify it still works with fallback
        assert result.current_step == "plan_step"
        assert result.result.status == "success"
        
        # The fallback message should be generated and stored in the context
        # This is tested indirectly through the successful execution
