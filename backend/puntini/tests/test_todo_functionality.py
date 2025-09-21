"""Test todo list functionality across all nodes.

This module tests the todo list functionality implemented in the GoalSpec model
and its integration with the parse_goal, plan_step, and evaluate nodes.
"""

import pytest
from unittest.mock import Mock, patch
from typing import Dict, Any

from ..models.goal_schemas import GoalSpec, TodoItem, TodoStatus, GoalComplexity, EntitySpec, EntityType
from ..nodes.parse_goal import parse_goal
from ..nodes.plan_step import plan_step, _format_todo_list
from ..nodes.evaluate import evaluate, _mark_todo_done, _mark_todo_done_in_state, _is_todo_completed_by_tool
from ..nodes.plan_step import _format_todo_list_from_state


class TestTodoFunctionality:
    """Test suite for todo list functionality."""
    
    def test_goal_spec_todo_management(self):
        """Test basic todo list management in GoalSpec."""
        # Create a GoalSpec with todo list
        todo1 = TodoItem(
            description="create the Project entity",
            status=TodoStatus.PLANNED,
            step_number=1,
            tool_name="add_node",
            estimated_complexity="medium"
        )
        
        todo2 = TodoItem(
            description="add relationship between User and Project",
            status=TodoStatus.PLANNED,
            step_number=2,
            tool_name="add_edge",
            estimated_complexity="low"
        )
        
        goal_spec = GoalSpec(
            original_goal="Create a project management system",
            intent="Set up basic project entities and relationships",
            complexity=GoalComplexity.MEDIUM,
            confidence=0.8,
            todo_list=[todo1, todo2]
        )
        
        # Test todo retrieval
        assert len(goal_spec.get_remaining_todos()) == 2
        assert len(goal_spec.get_completed_todos()) == 0
        assert not goal_spec.is_goal_complete()
        
        # Test marking todo as done
        assert goal_spec.mark_todo_done("create the Project entity")
        assert len(goal_spec.get_remaining_todos()) == 1
        assert len(goal_spec.get_completed_todos()) == 1
        assert not goal_spec.is_goal_complete()
        
        # Test marking second todo as done
        assert goal_spec.mark_todo_done("add relationship between User and Project")
        assert len(goal_spec.get_remaining_todos()) == 0
        assert len(goal_spec.get_completed_todos()) == 2
        assert goal_spec.is_goal_complete()
    
    def test_format_todo_list(self):
        """Test formatting todo list for LLM prompts."""
        parsed_goal_data = {
            "todo_list": [
                {
                    "description": "create the Project entity",
                    "status": "planned",
                    "step_number": 1,
                    "tool_name": "add_node",
                    "estimated_complexity": "medium"
                },
                {
                    "description": "add relationship between User and Project",
                    "status": "done",
                    "step_number": 2,
                    "tool_name": "add_edge",
                    "estimated_complexity": "low"
                }
            ]
        }
        
        formatted = _format_todo_list(parsed_goal_data)
        
        assert "1. create the Project entity" in formatted
        assert "Status: planned" in formatted
        assert "Tool: add_node" in formatted
        assert "Complexity: medium" in formatted
        assert "2. add relationship between User and Project" in formatted
        assert "Status: done" in formatted
    
    def test_format_empty_todo_list(self):
        """Test formatting empty todo list."""
        parsed_goal_data = {"todo_list": []}
        formatted = _format_todo_list(parsed_goal_data)
        assert formatted == "No todo list available"
    
    def test_is_todo_completed_by_tool(self):
        """Test matching todo descriptions to tool executions."""
        # Test add_node tool matching
        assert _is_todo_completed_by_tool("create the Project entity", "add_node", {})
        assert _is_todo_completed_by_tool("add new node", "add_node", {})
        assert not _is_todo_completed_by_tool("delete something", "add_node", {})
        
        # Test add_edge tool matching
        assert _is_todo_completed_by_tool("connect User to Project", "add_edge", {})
        assert _is_todo_completed_by_tool("add relationship", "add_edge", {})
        assert not _is_todo_completed_by_tool("create node", "add_edge", {})
        
        # Test query tools matching
        assert _is_todo_completed_by_tool("find all users", "query_graph", {})
        assert _is_todo_completed_by_tool("search for projects", "cypher_query", {})
    
    def test_mark_todo_done_with_matching_tool(self):
        """Test marking todo as done when tool matches."""
        state_dict = {
            "todo_list": [
                {
                    "description": "create the Project entity",
                    "status": "planned",
                    "tool_name": "add_node"
                }
            ]
        }
        
        result = {"status": "success"}
        todo_description = _mark_todo_done_in_state(state_dict, "add_node", result)
        
        assert todo_description == "create the Project entity"
        # Verify the todo was marked as done
        todo_list = state_dict["todo_list"]
        assert todo_list[0]["status"] == "done"
    
    def test_mark_todo_done_with_description_matching(self):
        """Test marking todo as done when description matches tool."""
        state_dict = {
            "todo_list": [
                {
                    "description": "create the Project entity",
                    "status": "planned",
                    "tool_name": "add_node"  # Tool name must match for the new logic
                }
            ]
        }
        
        result = {"status": "success"}
        todo_description = _mark_todo_done_in_state(state_dict, "add_node", result)
        
        assert todo_description == "create the Project entity"
        # Verify the todo was marked as done
        todo_list = state_dict["todo_list"]
        assert todo_list[0]["status"] == "done"
    
    def test_mark_todo_done_no_match(self):
        """Test when no todo matches the tool execution."""
        state_dict = {
            "todo_list": [
                {
                    "description": "delete something",
                    "status": "planned",
                    "tool_name": "add_node"
                }
            ]
        }
        
        result = {"status": "success"}
        todo_description = _mark_todo_done(state_dict, "add_node", result)
        
        assert todo_description is None
        # Verify the todo was not marked as done
        todo_list = state_dict["todo_list"]
        assert todo_list[0]["status"] == "planned"
    
    def test_mark_todo_done_already_done(self):
        """Test that already done todos are not updated."""
        state_dict = {
            "todo_list": [
                {
                    "description": "create the Project entity",
                    "status": "done",
                    "tool_name": "add_node"
                }
            ]
        }
        
        result = {"status": "success"}
        todo_description = _mark_todo_done(state_dict, "add_node", result)
        
        assert todo_description is None
        # Verify the todo status remains done
        todo_list = state_dict["todo_list"]
        assert todo_list[0]["status"] == "done"
    
    def test_mark_todo_done_no_artifacts(self):
        """Test when no todo list is available."""
        state_dict = {}
        result = {"status": "success"}
        todo_description = _mark_todo_done(state_dict, "add_node", result)
        assert todo_description is None
    
    def test_mark_todo_done_no_todo_list(self):
        """Test when state has no todo list."""
        state_dict = {"todo_list": []}
        result = {"status": "success"}
        todo_description = _mark_todo_done(state_dict, "add_node", result)
        assert todo_description is None
    
    def test_format_todo_list_from_state(self):
        """Test formatting todo list from state objects."""
        # Test with TodoItem objects
        todo_items = [
            TodoItem(
                description="create the Project entity",
                status=TodoStatus.PLANNED,
                step_number=1,
                tool_name="add_node",
                estimated_complexity="medium"
            ),
            TodoItem(
                description="add relationship between User and Project",
                status=TodoStatus.DONE,
                step_number=2,
                tool_name="add_edge",
                estimated_complexity="low"
            )
        ]
        
        formatted = _format_todo_list_from_state(todo_items)
        
        assert "1. create the Project entity" in formatted
        assert "Status: TodoStatus.PLANNED" in formatted
        assert "Tool: add_node" in formatted
        assert "Complexity: medium" in formatted
        assert "2. add relationship between User and Project" in formatted
        assert "Status: TodoStatus.DONE" in formatted
    
    def test_format_todo_list_from_state_dict(self):
        """Test formatting todo list from state dictionary format."""
        # Test with dictionary format
        todo_items = [
            {
                "description": "create the Project entity",
                "status": "planned",
                "step_number": 1,
                "tool_name": "add_node",
                "estimated_complexity": "medium"
            }
        ]
        
        formatted = _format_todo_list_from_state(todo_items)
        
        assert "1. create the Project entity" in formatted
        assert "Status: planned" in formatted
        assert "Tool: add_node" in formatted
        assert "Complexity: medium" in formatted
    
    def test_mark_todo_done_in_state(self):
        """Test marking todo as done in state."""
        state_dict = {
            "todo_list": [
                {
                    "description": "create the Project entity",
                    "status": "planned",
                    "tool_name": "add_node"
                }
            ]
        }
        
        result = {"status": "success"}
        todo_description = _mark_todo_done_in_state(state_dict, "add_node", result)
        
        assert todo_description == "create the Project entity"
        # Verify the todo was marked as done in state
        todo_list = state_dict["todo_list"]
        assert todo_list[0]["status"] == "done"
    
    def test_mark_todo_done_in_state_no_match(self):
        """Test when no todo matches the tool execution in state."""
        state_dict = {
            "todo_list": [
                {
                    "description": "delete something",
                    "status": "planned",
                    "tool_name": "add_node"
                }
            ]
        }
        
        result = {"status": "success"}
        todo_description = _mark_todo_done_in_state(state_dict, "add_node", result)
        
        assert todo_description is None
        # Verify the todo was not marked as done
        todo_list = state_dict["todo_list"]
        assert todo_list[0]["status"] == "planned"
    
    def test_mark_todo_done_in_state_no_todo_list(self):
        """Test when state has no todo list."""
        state_dict = {}
        result = {"status": "success"}
        todo_description = _mark_todo_done_in_state(state_dict, "add_node", result)
        assert todo_description is None


if __name__ == "__main__":
    pytest.main([__file__])
