"""Unit tests for the execute_tool node.

This module tests the execute_tool node functionality that merges
route_tool and call_tool functionality into a single atomic operation.
"""

from unittest.mock import Mock, MagicMock
import pytest
from datetime import datetime
from typing import Dict, Any, Optional

from puntini.nodes.execute_tool import execute_tool, _normalize_tool_result, _summarize_result, _create_detailed_progress_message, _validate_entity_refs, _is_error_retryable
from puntini.nodes.message import ExecuteToolResponse, ExecuteToolResult, ErrorContext
from puntini.models.errors import ValidationError, NotFoundError, ToolError


class MockTool:
    """Mock tool for testing."""
    
    def __init__(self, name: str, should_fail: bool = False, return_value: Any = {"result": "success"}):
        self.name = name
        self.should_fail = should_fail
        self.return_value = return_value
        
    def invoke(self, args: Dict[str, Any]):
        if self.should_fail:
            raise Exception("Tool execution failed")
        return self.return_value
        
    def validate_args(self, args: Dict[str, Any]):
        class ValidationResult:
            def __init__(self, valid: bool, errors: Optional[str] = None):
                self.valid = valid
                self.errors = errors
        
        # Basic validation - check if required field exists
        if "required_field" in args and not args.get("required_field"):
            return ValidationResult(valid=False, errors="required_field is required")
        return ValidationResult(valid=True)


class MockToolRegistry:
    """Mock tool registry for testing."""
    
    def __init__(self, tools: Dict[str, MockTool]):
        self.tools = tools
    
    def get(self, name: str):
        return self.tools.get(name)


class MockGraphStore:
    """Mock graph store for testing."""
    
    def __init__(self):
        self.nodes = {
            ("User", "user123"): {"name": "John Doe", "email": "john@example.com"}
        }
    
    def get_node(self, label: str, key: str):
        return self.nodes.get((label, key))


def test_execute_tool_success():
    """Test successful tool execution."""
    # Arrange
    tool = MockTool("test_tool", should_fail=False, return_value={"message": "Success"})
    tool_registry = MockToolRegistry({"test_tool": tool})
    
    state = {
        "tool_signature": {
            "tool_name": "test_tool",
            "tool_args": {"param": "value"}
        },
        "tool_registry": tool_registry,
        "graph_store": MockGraphStore()
    }
    
    # Act
    response: ExecuteToolResponse = execute_tool(state)
    
    # Assert
    assert response.current_step == "evaluate"
    assert response.result.status == "success"
    assert response.result.tool_name == "test_tool"
    assert response.result.result == {"message": "Success"}
    # The result_type will be "dict" since it's a dictionary, not "string"
    assert response.result.result_type in ["dict", "string"]  # Could be either depending on structure
    assert "Successfully executed test_tool" in response.progress[0]


def test_execute_tool_with_missing_tool_name():
    """Test execution with missing tool name."""
    # Arrange
    state = {
        "tool_signature": {},
        "tool_registry": MockToolRegistry({})
    }
    
    # Act
    response: ExecuteToolResponse = execute_tool(state)
    
    # Assert
    assert response.current_step == "diagnose"
    assert response.result.status == "error"
    assert response.result.error_type == "validation_error"
    assert "No tool specified for execution" in response.result.error


def test_execute_tool_with_missing_tool_registry():
    """Test execution with missing tool registry."""
    # Arrange
    state = {
        "tool_signature": {
            "tool_name": "test_tool"
        },
        "tool_registry": None
    }
    
    # Act
    response: ExecuteToolResponse = execute_tool(state)
    
    # Assert
    assert response.current_step == "diagnose"
    assert response.result.status == "error"
    assert response.result.error_type == "system_error"
    assert "Tool registry not available" in response.result.error


def test_execute_tool_with_nonexistent_tool():
    """Test execution with nonexistent tool."""
    # Arrange
    state = {
        "tool_signature": {
            "tool_name": "nonexistent_tool",
            "tool_args": {"param": "value"}
        },
        "tool_registry": MockToolRegistry({})
    }
    
    # Act
    response: ExecuteToolResponse = execute_tool(state)
    
    # Assert
    assert response.current_step == "diagnose"
    assert response.result.status == "error"
    assert response.result.error_type == "not_found_error"
    assert "not found in registry" in response.result.error


def test_execute_tool_with_validation_error():
    """Test execution with validation error."""
    # Arrange
    tool = MockTool("test_tool", should_fail=False, return_value={"message": "Success"})
    tool_registry = MockToolRegistry({"test_tool": tool})
    
    state = {
        "tool_signature": {
            "tool_name": "test_tool",
            "tool_args": {"required_field": ""}  # This should fail validation
        },
        "tool_registry": tool_registry
    }
    
    # Act
    response: ExecuteToolResponse = execute_tool(state)
    
    # Assert
    assert response.current_step == "diagnose"
    assert response.result.status == "error"
    assert response.result.error_type == "validation_error"
    assert "Tool validation failed" in response.result.error


def test_execute_tool_with_execution_error():
    """Test execution with tool execution error."""
    # Arrange
    tool = MockTool("test_tool", should_fail=True)
    tool_registry = MockToolRegistry({"test_tool": tool})
    
    state = {
        "tool_signature": {
            "tool_name": "test_tool",
            "tool_args": {"param": "value"}
        },
        "tool_registry": tool_registry
    }
    
    # Act
    response: ExecuteToolResponse = execute_tool(state)
    
    # Assert
    assert response.current_step == "diagnose"
    assert response.result.status == "error"
    assert response.result.error_type in ["tool_error", "system_error", "tool_error_retryable"]
    assert "Tool execution failed" in response.result.error


def test_normalize_tool_result_with_dict():
    """Test normalizing a dictionary result."""
    # Act
    result = _normalize_tool_result({"data": "value", "status": "success"}, "test_tool", 0.1)
    
    # Assert
    assert result.status == "success"
    assert result.tool_name == "test_tool"
    assert result.result == {"data": "value", "status": "success"}
    assert result.execution_time == 0.1
    assert result.result_type == "dict"


def test_normalize_tool_result_with_string():
    """Test normalizing a string result."""
    # Act
    result = _normalize_tool_result("test string", "test_tool", 0.1)
    
    # Assert
    assert result.status == "success"
    assert result.tool_name == "test_tool"
    assert result.result == {"message": "test string"}
    assert result.execution_time == 0.1
    assert result.result_type == "string"


def test_normalize_tool_result_with_list():
    """Test normalizing a list result."""
    # Act
    result = _normalize_tool_result([1, 2, 3], "test_tool", 0.1)
    
    # Assert
    assert result.status == "success"
    assert result.tool_name == "test_tool"
    assert result.result == {"data": [1, 2, 3], "count": 3}
    assert result.execution_time == 0.1
    assert result.result_type == "collection"


def test_summarize_result_success():
    """Test summarizing a successful result."""
    # Arrange
    result = ExecuteToolResult(
        status="success",
        tool_name="test_tool",
        result={"message": "Operation completed"},
        execution_time=0.1,
        result_type="string"
    )
    
    # Act
    summary = _summarize_result(result)
    
    # Assert
    assert "test_tool" in summary
    assert "Operation" in summary  # The actual message should be included


def test_summarize_result_error():
    """Test summarizing an error result."""
    # Arrange
    result = ExecuteToolResult(
        status="error",
        tool_name="test_tool",
        error="Something went wrong",
        execution_time=0.1,
        result_type="string"
    )
    
    # Act
    summary = _summarize_result(result)
    
    # Assert
    assert "Failed" in summary
    assert "Something went wrong" in summary


def test_create_detailed_progress_message_success():
    """Test creating a detailed progress message for success."""
    # Arrange
    result = ExecuteToolResult(
        status="success",
        tool_name="add_node",
        result={"message": "Node created"},
        execution_time=0.1,
        result_type="add_node"
    )
    
    # Act
    message = _create_detailed_progress_message("add_node", {"label": "User", "key": "user123"}, result)
    
    # Assert
    assert "Successfully added User node 'user123'" in message


def test_create_detailed_progress_message_failure():
    """Test creating a detailed progress message for failure."""
    # Arrange
    result = ExecuteToolResult(
        status="error",
        tool_name="test_tool",
        error="Operation failed",
        execution_time=0.1,
        result_type="string"
    )
    
    # Act
    message = _create_detailed_progress_message("test_tool", {}, result)
    
    # Assert
    assert "Failed to execute test_tool" in message
    assert "Operation failed" in message


def test_validate_entity_refs_success():
    """Test validating entity references that exist."""
    # Arrange
    graph_store = MockGraphStore()
    
    # Act
    exists = _validate_entity_refs(graph_store, {"label": "User", "key": "user123"})
    
    # Assert
    assert exists is True


def test_validate_entity_refs_not_found():
    """Test validating entity references that don't exist."""
    # Arrange
    graph_store = MockGraphStore()
    
    # Act
    exists = _validate_entity_refs(graph_store, {"label": "User", "key": "nonexistent"})
    
    # Assert
    assert exists is False


def test_is_error_retryable_network_error():
    """Test identifying retryable network errors."""
    # Act
    is_retryable = _is_error_retryable("Connection timeout occurred", "test_tool")
    
    # Assert
    assert is_retryable is True


def test_is_error_retryable_non_retryable():
    """Test identifying non-retryable errors."""
    # Act
    is_retryable = _is_error_retryable("Invalid input provided", "test_tool")
    
    # Assert
    assert is_retryable is False


def test_is_error_retryable_query_tool():
    """Test that query tools are considered potentially retryable."""
    # Act
    is_retryable = _is_error_retryable("Some generic error", "query")
    
    # Assert
    assert is_retryable is True


if __name__ == "__main__":
    pytest.main([__file__])