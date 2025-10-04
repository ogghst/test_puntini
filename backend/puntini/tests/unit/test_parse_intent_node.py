"""Tests for parse_intent node implementation.

This module tests the parse_intent node that implements Phase 1 of the
two-phase parsing architecture.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate

from puntini.nodes.parse_intent import parse_intent
from puntini.models.intent_schemas import IntentSpec, IntentType
from puntini.models.goal_schemas import GoalComplexity
from puntini.models.errors import ValidationError


class TestParseIntentNode:
    """Test cases for parse_intent node."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_llm = Mock()
        self.mock_runtime = Mock()
        self.mock_runtime.context = {"llm": self.mock_llm}
        
        self.valid_state = {
            "goal": "Create a user John for Project Alpha",
            "current_attempt": 1
        }
    
    @patch('puntini.nodes.parse_intent.ChatPromptTemplate')
    def test_parse_intent_success(self, mock_prompt_template):
        """Test successful intent parsing."""
        # Mock the structured LLM response
        mock_intent_spec = IntentSpec(
            intent_type=IntentType.CREATE,
            mentioned_entities=["John", "Project Alpha"],
            requires_graph_context=True,
            complexity=GoalComplexity.MEDIUM,
            original_goal="Create a user John for Project Alpha"
        )
        
        # Mock the entire chain (prompt | structured_llm)
        mock_chain = Mock()
        mock_chain.invoke.return_value = mock_intent_spec
        
        # Mock the prompt template
        mock_prompt = Mock()
        mock_prompt.__or__ = Mock(return_value=mock_chain)  # Mock the | operator
        mock_prompt_template.from_messages.return_value = mock_prompt
        
        # Mock the structured LLM
        mock_structured_llm = Mock()
        self.mock_llm.with_structured_output.return_value = mock_structured_llm
        
        # Call the function
        result = parse_intent(self.valid_state, runtime=self.mock_runtime)
        
        # Verify the result
        assert result.current_step == "resolve_entities"  # Should route to entity resolution
        assert result.current_attempt == 1
        assert result.result.status == "success"
        assert result.result.parsed_goal["intent_type"] == "create"
        assert result.result.parsed_goal["mentioned_entities"] == ["John", "Project Alpha"]
        assert result.result.requires_graph_ops is True
        assert result.result.is_simple is False
        
        # Verify LLM was called correctly
        self.mock_llm.with_structured_output.assert_called_once_with(IntentSpec)
        mock_chain.invoke.assert_called_once_with({"goal": "Create a user John for Project Alpha"})
    
    @patch('puntini.nodes.parse_intent.ChatPromptTemplate')
    def test_parse_intent_simple_goal(self, mock_prompt_template):
        """Test parsing a simple goal that doesn't require graph context."""
        # Mock the structured LLM response for a simple goal
        mock_intent_spec = IntentSpec(
            intent_type=IntentType.QUERY,
            mentioned_entities=["users"],
            requires_graph_context=False,
            complexity=GoalComplexity.SIMPLE,
            original_goal="Show me all users"
        )
        
        # Mock the entire chain (prompt | structured_llm)
        mock_chain = Mock()
        mock_chain.invoke.return_value = mock_intent_spec
        
        # Mock the prompt template
        mock_prompt = Mock()
        mock_prompt.__or__ = Mock(return_value=mock_chain)  # Mock the | operator
        mock_prompt_template.from_messages.return_value = mock_prompt
        
        # Mock the structured LLM
        mock_structured_llm = Mock()
        self.mock_llm.with_structured_output.return_value = mock_structured_llm
        
        # Call the function
        result = parse_intent(self.valid_state, runtime=self.mock_runtime)
        
        # Verify the result
        assert result.current_step == "plan_step"  # Should route directly to planning
        assert result.result.status == "success"
        assert result.result.requires_graph_ops is False
        assert result.result.is_simple is True
    
    def test_parse_intent_validation_error(self):
        """Test handling of validation errors."""
        # Test with invalid state
        invalid_state = {
            "goal": "",  # Empty goal
            "current_attempt": 1
        }
        
        # Should raise ValidationError for empty goal
        with pytest.raises(ValidationError, match="Goal cannot be empty"):
            parse_intent(invalid_state, runtime=self.mock_runtime)
    
    def test_parse_intent_no_llm_in_context(self):
        """Test handling when LLM is not in runtime context."""
        # Mock runtime without LLM
        mock_runtime_no_llm = Mock()
        mock_runtime_no_llm.context = {}
        
        result = parse_intent(self.valid_state, runtime=mock_runtime_no_llm)
        
        # Verify error handling
        assert result.current_step == "escalate"
        assert result.result.status == "error"
        assert result.result.retryable is False
        assert "LLM not configured" in result.result.error
    
    def test_parse_intent_no_runtime(self):
        """Test handling when runtime is None."""
        with patch('puntini.nodes.parse_intent.get_runtime') as mock_get_runtime:
            mock_get_runtime.side_effect = Exception("Runtime not available")
            
            result = parse_intent(self.valid_state, runtime=None)
            
            # Verify error handling
            assert result.current_step == "escalate"
            assert result.result.status == "error"
            assert result.result.retryable is False
            assert "Runtime context not available" in result.result.error
    
    @patch('puntini.nodes.parse_intent.ChatPromptTemplate')
    def test_parse_intent_llm_parsing_error(self, mock_prompt_template):
        """Test handling of LLM parsing errors."""
        # Mock LLM to raise a JSON parsing error
        mock_chain = Mock()
        mock_chain.invoke.side_effect = Exception("JSONDecodeError: Expecting value")
        
        # Mock the prompt template
        mock_prompt = Mock()
        mock_prompt.__or__ = Mock(return_value=mock_chain)  # Mock the | operator
        mock_prompt_template.from_messages.return_value = mock_prompt
        
        # Mock the structured LLM
        mock_structured_llm = Mock()
        self.mock_llm.with_structured_output.return_value = mock_structured_llm
        
        result = parse_intent(self.valid_state, runtime=self.mock_runtime)
        
        # Verify error handling
        assert result.current_step == "escalate"
        assert result.result.status == "error"
        assert result.result.retryable is False
        assert "LLM response was truncated" in result.result.error
    
    @patch('puntini.nodes.parse_intent.ChatPromptTemplate')
    def test_parse_intent_network_error_retryable(self, mock_prompt_template):
        """Test handling of network errors that are retryable."""
        # Mock LLM to raise a network error
        mock_chain = Mock()
        mock_chain.invoke.side_effect = Exception("Connection timeout")
        
        # Mock the prompt template
        mock_prompt = Mock()
        mock_prompt.__or__ = Mock(return_value=mock_chain)  # Mock the | operator
        mock_prompt_template.from_messages.return_value = mock_prompt
        
        # Mock the structured LLM
        mock_structured_llm = Mock()
        self.mock_llm.with_structured_output.return_value = mock_structured_llm
        
        result = parse_intent(self.valid_state, runtime=self.mock_runtime)
        
        # Verify error handling
        assert result.current_step == "diagnose"
        assert result.current_attempt == 2
        assert result.result.status == "error"
        assert result.result.retryable is True
        assert "network_error" in result.failures[0].error_type
    
    def test_parse_intent_multiple_attempts_failure(self):
        """Test handling when multiple attempts fail."""
        # Mock LLM to raise a network error
        self.mock_llm.with_structured_output.return_value.invoke.side_effect = Exception("Connection timeout")
        
        # Test with current_attempt > 1
        state_with_retry = {
            "goal": "Create a user John",
            "current_attempt": 2
        }
        
        result = parse_intent(state_with_retry, runtime=self.mock_runtime)
        
        # Verify error handling
        assert result.current_step == "escalate"
        assert result.current_attempt == 2
        assert result.result.status == "error"
        assert result.result.retryable is True
    
    @patch('puntini.nodes.parse_intent.ChatPromptTemplate')
    def test_parse_intent_no_meaningful_intent(self, mock_prompt_template):
        """Test handling when no meaningful intent is extracted."""
        # Mock the structured LLM response with unknown intent
        mock_intent_spec = IntentSpec(
            intent_type=IntentType.UNKNOWN,
            mentioned_entities=[],
            requires_graph_context=False,
            complexity=GoalComplexity.SIMPLE,
            original_goal="What's the weather?"
        )
        
        # Mock the entire chain (prompt | structured_llm)
        mock_chain = Mock()
        mock_chain.invoke.return_value = mock_intent_spec
        
        # Mock the prompt template
        mock_prompt = Mock()
        mock_prompt.__or__ = Mock(return_value=mock_chain)  # Mock the | operator
        mock_prompt_template.from_messages.return_value = mock_prompt
        
        # Mock the structured LLM
        mock_structured_llm = Mock()
        self.mock_llm.with_structured_output.return_value = mock_structured_llm
        
        result = parse_intent(self.valid_state, runtime=self.mock_runtime)
        
        # Verify error handling
        assert result.current_step == "escalate"
        assert result.result.status == "error"
        assert result.result.retryable is False
        assert "Could not extract meaningful intent" in result.result.error
    
    @patch('puntini.nodes.parse_intent.ChatPromptTemplate')
    def test_parse_intent_routing_logic(self, mock_prompt_template):
        """Test the routing logic for different intent types."""
        test_cases = [
            # (intent_type, requires_graph_context, complexity, expected_route)
            (IntentType.CREATE, True, GoalComplexity.MEDIUM, "resolve_entities"),
            (IntentType.QUERY, False, GoalComplexity.SIMPLE, "plan_step"),
            (IntentType.UPDATE, True, GoalComplexity.COMPLEX, "resolve_entities"),
            (IntentType.DELETE, False, GoalComplexity.SIMPLE, "plan_step"),
        ]
        
        for intent_type, requires_graph_context, complexity, expected_route in test_cases:
            # Mock the structured LLM response
            mock_intent_spec = IntentSpec(
                intent_type=intent_type,
                mentioned_entities=["test"],
                requires_graph_context=requires_graph_context,
                complexity=complexity,
                original_goal="Test goal"
            )
            
            # Mock the entire chain (prompt | structured_llm)
            mock_chain = Mock()
            mock_chain.invoke.return_value = mock_intent_spec
            
            # Mock the prompt template
            mock_prompt = Mock()
            mock_prompt.__or__ = Mock(return_value=mock_chain)  # Mock the | operator
            mock_prompt_template.from_messages.return_value = mock_prompt
            
            # Mock the structured LLM
            mock_structured_llm = Mock()
            self.mock_llm.with_structured_output.return_value = mock_structured_llm
            
            # Call the function
            result = parse_intent(self.valid_state, runtime=self.mock_runtime)
            
            # Verify routing
            assert result.current_step == expected_route, f"Failed for {intent_type}, {requires_graph_context}, {complexity}"
    
    @patch('puntini.nodes.parse_intent.ChatPromptTemplate')
    def test_parse_intent_progress_tracking(self, mock_prompt_template):
        """Test that progress is properly tracked."""
        # Mock the structured LLM response
        mock_intent_spec = IntentSpec(
            intent_type=IntentType.CREATE,
            mentioned_entities=["John"],
            requires_graph_context=True,
            complexity=GoalComplexity.SIMPLE,
            original_goal="Create user John"
        )
        
        # Mock the entire chain (prompt | structured_llm)
        mock_chain = Mock()
        mock_chain.invoke.return_value = mock_intent_spec
        
        # Mock the prompt template
        mock_prompt = Mock()
        mock_prompt.__or__ = Mock(return_value=mock_chain)  # Mock the | operator
        mock_prompt_template.from_messages.return_value = mock_prompt
        
        # Mock the structured LLM
        mock_structured_llm = Mock()
        self.mock_llm.with_structured_output.return_value = mock_structured_llm
        
        # Call the function
        result = parse_intent(self.valid_state, runtime=self.mock_runtime)
        
        # Verify progress tracking
        assert len(result.progress) == 1
        assert "Parsed intent: create" in result.progress[0]
    
    @patch('puntini.nodes.parse_intent.ChatPromptTemplate')
    def test_parse_intent_artifacts_and_failures(self, mock_prompt_template):
        """Test that artifacts and failures are properly handled."""
        # Mock the structured LLM response
        mock_intent_spec = IntentSpec(
            intent_type=IntentType.CREATE,
            mentioned_entities=["John"],
            requires_graph_context=True,
            complexity=GoalComplexity.SIMPLE,
            original_goal="Create user John"
        )
        
        # Mock the entire chain (prompt | structured_llm)
        mock_chain = Mock()
        mock_chain.invoke.return_value = mock_intent_spec
        
        # Mock the prompt template
        mock_prompt = Mock()
        mock_prompt.__or__ = Mock(return_value=mock_chain)  # Mock the | operator
        mock_prompt_template.from_messages.return_value = mock_prompt
        
        # Mock the structured LLM
        mock_structured_llm = Mock()
        self.mock_llm.with_structured_output.return_value = mock_structured_llm
        
        # Call the function
        result = parse_intent(self.valid_state, runtime=self.mock_runtime)
        
        # Verify artifacts and failures
        assert result.artifacts == []  # No artifacts for intent parsing
        assert result.failures == []  # No failures for successful parsing
