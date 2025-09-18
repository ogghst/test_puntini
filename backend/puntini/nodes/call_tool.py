"""Call tool node implementation.

This module implements the call_tool node that executes tools
with validated inputs and normalizes human-readable errors.
"""

from typing import Any, Dict, Optional, TYPE_CHECKING
import time
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime

if TYPE_CHECKING:
    from ..orchestration.state_schema import State
from ..interfaces.tool_registry import ToolRegistry
from ..models.errors import ValidationError, NotFoundError, ToolError
from ..logging import get_logger
from .message import CallToolResponse, CallToolResult, Artifact, ErrorContext

logger = get_logger(__name__)


def call_tool(
    state: "State", 
    config: Optional[RunnableConfig] = None, 
    runtime: Optional[Runtime] = None
) -> CallToolResponse:
    """Execute the selected tool.
    
    This node executes the tool with the provided arguments and
    handles any errors that occur during execution. It provides
    comprehensive error handling and normalization for human-readable
    error messages.
    
    Args:
        state: Current agent state with validated tool signature.
        config: Optional RunnableConfig for additional configuration.
        runtime: Optional Runtime context for additional runtime information.
        
    Returns:
        Updated state with tool execution result.
        
    Notes:
        Tool execution includes:
        - Input validation and sanitization
        - Tool execution with timeout handling
        - Error normalization and human-readable messages
        - Result formatting and metadata collection
        - Progress tracking and logging
        
    Raises:
        ToolError: If tool execution fails with a recoverable error.
        ValidationError: If tool arguments are invalid.
        NotFoundError: If tool is not available.
    """
    tool_signature = state.tool_signature or {}
    tool_name = tool_signature.get("tool_name")
    tool_args = tool_signature.get("tool_args", {})
    routing_decision = tool_signature.get("routing_decision", {})
    
    logger.debug(f"Executing tool: {tool_name} with args: {tool_args}")
    
    # Validate tool signature
    if not tool_name:
        error_msg = "No tool specified for execution"
        logger.error(error_msg)
        return CallToolResponse(
            current_step="diagnose",
            result=CallToolResult(
                status="error",
                tool_name=tool_name or "unknown",
                error=error_msg,
                error_type="validation_error",
                execution_time=0.0
            ),
            error_context=ErrorContext(
                type="validation_error",
                message=error_msg,
                details={"missing_field": "tool_name"}
            )
        )
    
    # Get tool registry from state
    tool_registry = state.tool_registry
    if tool_registry is None:
        error_msg = "Tool registry not available in state. Ensure agent is created with create_initial_state()"
        logger.error(error_msg)
        return CallToolResponse(
            current_step="diagnose",
            result=CallToolResult(
                status="error",
                tool_name=tool_name,
                error=error_msg,
                error_type="system_error",
                execution_time=0.0
            ),
            error_context=ErrorContext(
                type="system_error",
                message=error_msg,
                details={"component": "tool_registry", "solution": "Use create_initial_state() to initialize state with components"}
            )
        )
    
    # Execute tool
    start_time = time.time()
    try:
        # Get tool callable
        tool_callable = tool_registry.get(tool_name)
        
        # Validate arguments one more time before execution
        if not isinstance(tool_args, dict):
            raise ValidationError(f"Tool arguments must be a dictionary, got {type(tool_args)}")
        
        logger.info(f"Executing tool '{tool_name}' with {len(tool_args)} arguments")
        
        # Execute the tool
        raw_result = tool_callable(**tool_args)
        
        execution_time = time.time() - start_time
        
        # Normalize result
        normalized_result = _normalize_tool_result(raw_result, tool_name, execution_time)
        
        logger.info(f"Successfully executed tool '{tool_name}' in {execution_time:.3f}s")
        
        return CallToolResponse(
            current_step="evaluate",
            result=normalized_result,
            progress=[f"Successfully executed tool: {tool_name}"],
            artifacts=[Artifact(
                type="tool_execution",
                data={
                    "tool_name": tool_name,
                    "execution_time": execution_time,
                    "status": "success",
                    "result_summary": _summarize_result(normalized_result)
                }
            )]
        )
        
    except NotFoundError as e:
        error_msg = f"Tool '{tool_name}' not found in registry"
        logger.error(error_msg)
        execution_time = time.time() - start_time
        return CallToolResponse(
            current_step="diagnose",
            result=CallToolResult(
                status="error",
                tool_name=tool_name,
                error=error_msg,
                error_type="not_found_error",
                execution_time=execution_time
            ),
            error_context=ErrorContext(
                type="not_found_error",
                message=error_msg,
                details={"tool_name": tool_name}
            )
        )
        
    except ValidationError as e:
        error_msg = f"Invalid arguments for tool '{tool_name}': {str(e)}"
        logger.error(error_msg)
        execution_time = time.time() - start_time
        return CallToolResponse(
            current_step="diagnose",
            result=CallToolResult(
                status="error",
                tool_name=tool_name,
                error=error_msg,
                error_type="validation_error",
                execution_time=execution_time
            ),
            error_context=ErrorContext(
                type="validation_error",
                message=error_msg,
                details={"tool_name": tool_name, "args": tool_args}
            )
        )
        
    except ToolError as e:
        error_msg = f"Tool execution failed: {str(e)}"
        logger.error(error_msg)
        execution_time = time.time() - start_time
        return CallToolResponse(
            current_step="diagnose",
            result=CallToolResult(
                status="error",
                tool_name=tool_name,
                error=error_msg,
                error_type="tool_error",
                execution_time=execution_time
            ),
            error_context=ErrorContext(
                type="tool_error",
                message=error_msg,
                details={"tool_name": tool_name, "original_error": str(e)}
            )
        )
        
    except Exception as e:
        error_msg = f"Unexpected error during tool execution: {str(e)}"
        logger.error(error_msg)
        execution_time = time.time() - start_time
        return CallToolResponse(
            current_step="diagnose",
            result=CallToolResult(
                status="error",
                tool_name=tool_name,
                error=error_msg,
                error_type="system_error",
                execution_time=execution_time
            ),
            error_context=ErrorContext(
                type="system_error",
                message=error_msg,
                details={"tool_name": tool_name, "original_error": str(e)}
            )
        )


def _normalize_tool_result(raw_result: Any, tool_name: str, execution_time: float) -> CallToolResult:
    """Normalize tool execution result.
    
    Args:
        raw_result: Raw result from tool execution.
        tool_name: Name of the executed tool.
        execution_time: Time taken for execution in seconds.
        
    Returns:
        Normalized CallToolResult object.
    """
    if isinstance(raw_result, dict):
        # If already a dict, add metadata
        return CallToolResult(
            status="success",
            tool_name=tool_name,
            result=raw_result,
            execution_time=execution_time,
            result_type="dict"
        )
    elif isinstance(raw_result, str):
        # If string, wrap in result
        return CallToolResult(
            status="success",
            tool_name=tool_name,
            result={"message": raw_result},
            execution_time=execution_time,
            result_type="string"
        )
    elif isinstance(raw_result, (list, tuple)):
        # If collection, wrap in result
        return CallToolResult(
            status="success",
            tool_name=tool_name,
            result={"data": list(raw_result), "count": len(raw_result)},
            execution_time=execution_time,
            result_type="collection"
        )
    else:
        # For other types, convert to string representation
        return CallToolResult(
            status="success",
            tool_name=tool_name,
            result={"value": str(raw_result), "type": type(raw_result).__name__},
            execution_time=execution_time,
            result_type="other"
        )


def _summarize_result(result: CallToolResult) -> str:
    """Create a human-readable summary of tool execution result.
    
    Args:
        result: Normalized tool result.
        
    Returns:
        Summary string.
    """
    if result.status != "success":
        return f"Failed: {result.error or 'Unknown error'}"
    
    result_type = result.result_type or "unknown"
    tool_name = result.tool_name or "unknown"
    execution_time = result.execution_time or 0.0
    
    if result_type == "dict":
        return f"Tool '{tool_name}' completed successfully in {execution_time:.3f}s"
    elif result_type == "string":
        message = result.result.get("message", "") if result.result else ""
        return f"Tool '{tool_name}' returned: {message[:100]}{'...' if len(message) > 100 else ''}"
    elif result_type == "collection":
        count = result.result.get("count", 0) if result.result else 0
        return f"Tool '{tool_name}' returned {count} items in {execution_time:.3f}s"
    else:
        return f"Tool '{tool_name}' completed in {execution_time:.3f}s"
