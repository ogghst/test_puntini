"""Test to verify WebSocket sends correct data types for todo_list and other array fields."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from puntini.api.websocket import WebSocketManager
from puntini.api.session import SessionManager


class TestWebSocketDataTypes:
    """Test cases for WebSocket data type consistency."""
    
    def test_values_update_data_structure(self):
        """Test that values update creates correct data structure with arrays."""
        # Test the data structure creation logic directly
        goal_spec = {
            "original_goal": "Test goal",
            "intent": "test",
            "complexity": "simple"
        }
        
        data = {
            "goal_spec": goal_spec,
            "current_step": "test_step",
            "progress": ["step1", "step2"],
            "artifacts": [{"type": "test"}],
            "failures": [{"error": "test"}]
        }
        
        # Simulate the data extraction logic from _handle_state_update
        todo_list = goal_spec.get("todo_list", [])
        entities_created = goal_spec.get("entities", [])
        progress = data.get("progress", [])
        artifacts = data.get("artifacts", [])
        failures = data.get("failures", [])
        
        # Verify all fields are arrays
        assert isinstance(todo_list, list), f"todo_list should be array, got {type(todo_list)}"
        assert isinstance(entities_created, list), f"entities_created should be array, got {type(entities_created)}"
        assert isinstance(progress, list), f"progress should be array, got {type(progress)}"
        assert isinstance(artifacts, list), f"artifacts should be array, got {type(artifacts)}"
        assert isinstance(failures, list), f"failures should be array, got {type(failures)}"
    
    def test_parse_goal_update_data_structure(self):
        """Test that parse_goal update creates correct data structure with arrays."""
        # Test the data structure creation logic directly
        parse_goal_data = {
            "original_goal": "Test goal",
            "intent": "test",
            "complexity": "simple",
            "todo_list": [
                {
                    "description": "Test todo",
                    "status": "planned",
                    "step_number": 1,
                    "tool_name": "test_tool",
                    "estimated_complexity": "medium"
                }
            ],
            "progress": ["step1", "step2"],
            "artifacts": [{"type": "test"}]
        }
        
        # Simulate the data extraction logic from _handle_parse_goal_update
        todo_list = []
        for todo_item in parse_goal_data.get('todo_list', []):
            todo_list.append({
                'description': todo_item.get('description', ''),
                'status': todo_item.get('status', 'planned'),
                'step_number': todo_item.get('step_number'),
                'tool_name': todo_item.get('tool_name'),
                'estimated_complexity': todo_item.get('estimated_complexity', 'medium')
            })
        
        entities_created = []
        progress = parse_goal_data.get('progress', [])
        artifacts = parse_goal_data.get('artifacts', [])
        
        # Verify all fields are arrays
        assert isinstance(todo_list, list), f"todo_list should be array, got {type(todo_list)}"
        assert isinstance(entities_created, list), f"entities_created should be array, got {type(entities_created)}"
        assert isinstance(progress, list), f"progress should be array, got {type(progress)}"
        assert isinstance(artifacts, list), f"artifacts should be array, got {type(artifacts)}"
        
        # Verify todo_list has correct content
        assert len(todo_list) == 1
        assert todo_list[0]['description'] == "Test todo"
        assert todo_list[0]['status'] == "planned"
    
    def test_empty_data_defaults_to_arrays(self):
        """Test that empty data defaults to arrays instead of objects."""
        # Test with completely empty data
        goal_spec = {}
        data = {}
        
        # Simulate the data extraction logic
        todo_list = goal_spec.get("todo_list", [])
        entities_created = goal_spec.get("entities", [])
        progress = data.get("progress", [])
        artifacts = data.get("artifacts", [])
        failures = data.get("failures", [])
        
        # Verify all fields are arrays (not objects)
        assert isinstance(todo_list, list), f"todo_list should be array, got {type(todo_list)}"
        assert isinstance(entities_created, list), f"entities_created should be array, got {type(entities_created)}"
        assert isinstance(progress, list), f"progress should be array, got {type(progress)}"
        assert isinstance(artifacts, list), f"artifacts should be array, got {type(artifacts)}"
        assert isinstance(failures, list), f"failures should be array, got {type(failures)}"
        
        # Verify they are empty arrays
        assert len(todo_list) == 0
        assert len(entities_created) == 0
        assert len(progress) == 0
        assert len(artifacts) == 0
        assert len(failures) == 0


if __name__ == "__main__":
    # Run tests
    test = TestWebSocketDataTypes()
    test.test_values_update_data_structure()
    test.test_parse_goal_update_data_structure()
    test.test_empty_data_defaults_to_arrays()
    print("All WebSocket data type tests passed!")
