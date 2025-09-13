"""Unit tests for the parse_goal node implementation.

This module tests the parse_goal node functionality including
LLM integration, structured output parsing, and error handling.
"""

import pytest
from unittest.mock import Mock, patch
from typing import Dict, Any

from puntini.nodes.parse_goal import parse_goal, _determine_next_step
from puntini.models.goal_schemas import GoalSpec, GoalComplexity, EntitySpec, EntityType
from puntini.models.errors import ValidationError


class TestParseGoal:
    """Test cases for the parse_goal function."""
    
    def test_parse_goal_empty_goal(self):
        """Test that empty goals raise ValidationError."""
        state = {"goal": "", "current_attempt": 1}
        
        with pytest.raises(ValidationError, match="Goal cannot be empty"):
            parse_goal(state)
    
    def test_parse_goal_whitespace_only(self):
        """Test that whitespace-only goals raise ValidationError."""
        state = {"goal": "   \n\t  ", "current_attempt": 1}
        
        with pytest.raises(ValidationError, match="Goal cannot be empty"):
            parse_goal(state)
    
    @patch('puntini.nodes.parse_goal.ChatOpenAI')
    @patch('puntini.nodes.parse_goal.ChatPromptTemplate')
    def test_parse_goal_success(self, mock_prompt, mock_llm):
        """Test successful goal parsing with mocked LLM."""
        # Mock the LLM response
        mock_goal_spec = GoalSpec(
            original_goal="Create a person node",
            intent="Create a person entity",
            complexity=GoalComplexity.SIMPLE,
            entities=[
                EntitySpec(
                    name="person",
                    type=EntityType.NODE,
                    label="Person"
                )
            ],
            constraints=[],
            domain_hints=[],
            estimated_steps=1,
            requires_human_input=False,
            priority="medium",
            confidence=0.9,
            parsing_notes=["Successfully parsed simple goal"]
        )
        
        # Mock the LLM chain
        mock_structured_llm = Mock()
        mock_structured_llm.invoke.return_value = mock_goal_spec
        mock_llm_instance = Mock()
        mock_llm_instance.with_structured_output.return_value = mock_structured_llm
        mock_llm.return_value = mock_llm_instance
        
        # Mock the prompt template
        mock_chain = Mock()
        mock_chain.invoke.return_value = mock_goal_spec
        mock_prompt.from_messages.return_value.__or__ = Mock(return_value=mock_chain)
        
        state = {
            "goal": "Create a person node called John",
            "current_attempt": 1
        }
        
        result = parse_goal(state)
        
        # Verify the result structure
        assert result["current_step"] == "route_tool"  # Simple goal should skip planning
        assert result["current_attempt"] == 1
        assert result["result"]["status"] == "success"
        assert result["result"]["complexity"] == GoalComplexity.SIMPLE
        assert result["result"]["is_simple"] is True
        assert len(result["progress"]) > 0
        assert len(result["artifacts"]) > 0
        
        # Verify LLM was called
        mock_llm.assert_called_once()
        mock_structured_llm.invoke.assert_called_once()
    
    @patch('puntini.nodes.parse_goal.ChatOpenAI')
    def test_parse_goal_llm_error_first_attempt(self, mock_llm):
        """Test handling of LLM errors on first attempt."""
        # Mock LLM to raise an exception
        mock_llm_instance = Mock()
        mock_llm_instance.with_structured_output.side_effect = Exception("LLM connection failed")
        mock_llm.return_value = mock_llm_instance
        
        state = {
            "goal": "Create a person node",
            "current_attempt": 1
        }
        
        result = parse_goal(state)
        
        # Should route to diagnose on first attempt failure
        assert result["current_step"] == "diagnose"
        assert result["current_attempt"] == 2
        assert result["result"]["status"] == "error"
        assert result["result"]["error_type"] == "parsing_error"
        assert len(result["failures"]) == 1
    
    @patch('puntini.nodes.parse_goal.ChatOpenAI')
    def test_parse_goal_llm_error_retry_attempt(self, mock_llm):
        """Test handling of LLM errors on retry attempt."""
        # Mock LLM to raise an exception
        mock_llm_instance = Mock()
        mock_llm_instance.with_structured_output.side_effect = Exception("LLM connection failed")
        mock_llm.return_value = mock_llm_instance
        
        state = {
            "goal": "Create a person node",
            "current_attempt": 2
        }
        
        result = parse_goal(state)
        
        # Should escalate after retry failure
        assert result["current_step"] == "escalate"
        assert result["current_attempt"] == 2
        assert result["result"]["status"] == "error"
        assert result["result"]["error_type"] == "parsing_error"
        assert len(result["failures"]) == 1
    
    @patch('puntini.nodes.parse_goal.ChatOpenAI')
    @patch('puntini.nodes.parse_goal.ChatPromptTemplate')
    def test_parse_goal_validation_error(self, mock_prompt, mock_llm):
        """Test handling of validation errors in parsed goal."""
        # Mock the LLM response with invalid data
        mock_goal_spec = GoalSpec(
            original_goal="Create a person node",
            intent="",  # Empty intent should cause validation error
            complexity=GoalComplexity.SIMPLE,
            entities=[],  # No entities
            constraints=[],
            domain_hints=[],
            estimated_steps=1,
            requires_human_input=False,
            priority="medium",
            confidence=0.9,
            parsing_notes=[]
        )
        
        # Mock the LLM chain
        mock_structured_llm = Mock()
        mock_structured_llm.invoke.return_value = mock_goal_spec
        mock_llm_instance = Mock()
        mock_llm_instance.with_structured_output.return_value = mock_structured_llm
        mock_llm.return_value = mock_llm_instance
        
        # Mock the prompt template
        mock_chain = Mock()
        mock_chain.invoke.return_value = mock_goal_spec
        mock_prompt.from_messages.return_value.__or__ = Mock(return_value=mock_chain)
        
        state = {
            "goal": "Create a person node",
            "current_attempt": 1
        }
        
        result = parse_goal(state)
        
        # Should handle validation error gracefully
        assert result["current_step"] == "diagnose"
        assert result["result"]["status"] == "error"
        assert "Could not extract meaningful entities or intent" in result["result"]["error"]


class TestDetermineNextStep:
    """Test cases for the _determine_next_step function."""
    
    def test_simple_goal_routes_to_route_tool(self):
        """Test that simple goals route directly to route_tool."""
        goal_spec = GoalSpec(
            original_goal="Create a node",
            intent="Create a simple node",
            complexity=GoalComplexity.SIMPLE,
            entities=[
                EntitySpec(name="node", type=EntityType.NODE)
            ],
            constraints=[],
            domain_hints=[],
            estimated_steps=1,
            requires_human_input=False,
            priority="medium",
            confidence=0.9,
            parsing_notes=[]
        )
        
        next_step = _determine_next_step(goal_spec, 1)
        assert next_step == "route_tool"
    
    def test_medium_complexity_routes_to_plan_step(self):
        """Test that medium complexity goals route to plan_step."""
        goal_spec = GoalSpec(
            original_goal="Create a complex graph",
            intent="Create a complex graph structure",
            complexity=GoalComplexity.MEDIUM,
            entities=[
                EntitySpec(name="node1", type=EntityType.NODE),
                EntitySpec(name="node2", type=EntityType.NODE),
                EntitySpec(name="edge", type=EntityType.EDGE)
            ],
            constraints=[],
            domain_hints=[],
            estimated_steps=3,
            requires_human_input=False,
            priority="medium",
            confidence=0.8,
            parsing_notes=[]
        )
        
        next_step = _determine_next_step(goal_spec, 1)
        assert next_step == "plan_step"
    
    def test_complex_goal_routes_to_plan_step(self):
        """Test that complex goals route to plan_step."""
        goal_spec = GoalSpec(
            original_goal="Create a very complex multi-step graph",
            intent="Create a complex multi-step graph",
            complexity=GoalComplexity.COMPLEX,
            entities=[
                EntitySpec(name="node1", type=EntityType.NODE),
                EntitySpec(name="node2", type=EntityType.NODE),
                EntitySpec(name="node3", type=EntityType.NODE),
                EntitySpec(name="edge1", type=EntityType.EDGE),
                EntitySpec(name="edge2", type=EntityType.EDGE)
            ],
            constraints=[],
            domain_hints=[],
            estimated_steps=5,
            requires_human_input=False,
            priority="high",
            confidence=0.7,
            parsing_notes=[]
        )
        
        next_step = _determine_next_step(goal_spec, 1)
        assert next_step == "plan_step"


@pytest.fixture
def sample_goal_specs():
    """Fixture providing sample goal specifications for testing."""
    return {
        "simple": GoalSpec(
            original_goal="Create a person node",
            intent="Create a person entity",
            complexity=GoalComplexity.SIMPLE,
            entities=[EntitySpec(name="person", type=EntityType.NODE, label="Person")],
            constraints=[],
            domain_hints=[],
            estimated_steps=1,
            requires_human_input=False,
            priority="medium",
            confidence=0.9,
            parsing_notes=[]
        ),
        "medium": GoalSpec(
            original_goal="Create a project with milestones",
            intent="Create a project management structure",
            complexity=GoalComplexity.MEDIUM,
            entities=[
                EntitySpec(name="project", type=EntityType.NODE, label="Project"),
                EntitySpec(name="milestone", type=EntityType.NODE, label="Milestone"),
                EntitySpec(name="depends_on", type=EntityType.EDGE)
            ],
            constraints=[],
            domain_hints=[],
            estimated_steps=3,
            requires_human_input=False,
            priority="medium",
            confidence=0.8,
            parsing_notes=[]
        ),
        "complex": GoalSpec(
            original_goal="Build a complete social network with users, posts, and interactions",
            intent="Create a comprehensive social network graph",
            complexity=GoalComplexity.COMPLEX,
            entities=[
                EntitySpec(name="user", type=EntityType.NODE, label="User"),
                EntitySpec(name="post", type=EntityType.NODE, label="Post"),
                EntitySpec(name="comment", type=EntityType.NODE, label="Comment"),
                EntitySpec(name="follows", type=EntityType.EDGE),
                EntitySpec(name="likes", type=EntityType.EDGE),
                EntitySpec(name="comments_on", type=EntityType.EDGE)
            ],
            constraints=[],
            domain_hints=[],
            estimated_steps=10,
            requires_human_input=True,
            priority="high",
            confidence=0.7,
            parsing_notes=[]
        )
    }
