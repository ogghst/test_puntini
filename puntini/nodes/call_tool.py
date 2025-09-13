"""Call tool node implementation.

This module implements the call_tool node that executes tools
with validated inputs and normalizes human-readable errors.
"""

from typing import Any, Dict
from ..orchestration.state import State
from ..tools.tool_registry_factory import create_standard_tool_registry
from ..models.specs import ToolSpec
from ..models.errors import NotFoundError

# Create a tool registry and register a dummy tool for now.
# In a real application, this would be initialized and populated
# at startup.
tool_registry = create_standard_tool_registry()

def dummy_tool(a: int, b: int) -> int:
    """A dummy tool that adds two numbers."""
    return a + b

tool_registry.register(ToolSpec(
    name="dummy_tool",
    description="A dummy tool that adds two numbers.",
    callable=dummy_tool,
    input_schema={"a": "int", "b": "int"}
))


def call_tool(state: State) -> Dict[str, Any]:
    """Execute the selected tool.
    
    This node executes the tool with the provided arguments and
    handles any errors that occur during execution.
    
    Args:
        state: Current agent state with tool signature.
        
    Returns:
        Updated state with tool execution result.
        
    Notes:
        Tool execution should be wrapped in error handling to
        provide human-readable error messages when failures occur.
    """
    tool_signature = state.get("_tool_signature", {})
    tool_name = tool_signature.get("tool_name")
    tool_args = tool_signature.get("tool_args", {})

    if not tool_name:
        result = {
            "status": "error",
            "tool_name": "unknown",
            "error": "Tool name not specified in the state.",
            "error_type": "configuration_error"
        }
    else:
        try:
            tool_to_call = tool_registry.get(tool_name)
            execution_result = tool_to_call(**tool_args)
            result = {
                "status": "success",
                "tool_name": tool_name,
                "result": execution_result,
            }
        except NotFoundError as e:
            result = {
                "status": "error",
                "tool_name": tool_name,
                "error": str(e),
                "error_type": "not_found_error"
            }
        except Exception as e:
            result = {
                "status": "error",
                "tool_name": tool_name,
                "error": str(e),
                "error_type": "execution_error"
            }
    
    return {
        "current_step": "evaluate",
        "result": result,
        "progress": state.get("progress", []) + [f"Executed tool: {tool_name}"]
    }
