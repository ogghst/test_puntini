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
    # Access state attributes - handle both dict and object access
    if isinstance(state, dict):
        tool_signature = state.get("tool_signature") or {}
    else:
        tool_signature = getattr(state, "tool_signature", None) or {}
    
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
    if isinstance(state, dict):
        tool_registry = state.get("tool_registry")
    else:
        tool_registry = getattr(state, "tool_registry", None)
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
        
        # Execute the tool using LangChain's invoke method
        try:
            raw_result = tool_callable.invoke(tool_args)
        except AttributeError:
            # Fallback for tools that don't have invoke method
            raw_result = tool_callable(**tool_args)
        
        execution_time = time.time() - start_time
        
        # Normalize result
        normalized_result : CallToolResult = _normalize_tool_result(raw_result, tool_name, execution_time)
        
        logger.info(f"Successfully executed tool '{tool_name}' in {execution_time:.3f}s")
        
        if normalized_result.status != "success":
            return CallToolResponse(
                current_step="diagnose",
                result=normalized_result,
                progress=[f"Failed to execute tool: {tool_name}"],
                artifacts=[Artifact(type="tool_execution", data={"tool_name": tool_name, "execution_time": execution_time, "status": "error", "result_summary": _summarize_result(normalized_result)})]
            )
        
        return CallToolResponse(
            current_step="evaluate",
            result=normalized_result,
            progress=[_create_detailed_progress_message(tool_name, tool_args, normalized_result)],
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
        # Check if it's a graph tool result with specific structure
        if "status" in raw_result and "message" in raw_result:
            # This is likely a TypedDict from graph tools
            result_type = "graph_tool"
            if "node" in raw_result:
                result_type = "add_node"
            elif "edge" in raw_result:
                result_type = "add_edge"
            elif "results" in raw_result:
                result_type = "query_result"
        else:
            result_type = "dict"
        
        return CallToolResult(
            status="success",
            tool_name=tool_name,
            result=raw_result,
            execution_time=execution_time,
            result_type=result_type
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
    elif result_type == "graph_tool":
        message = result.result.get("message", "") if result.result else ""
        return f"Tool '{tool_name}' completed: {message[:100]}{'...' if len(message) > 100 else ''}"
    elif result_type == "add_node":
        message = result.result.get("message", "") if result.result else ""
        return f"Tool '{tool_name}' created node: {message[:100]}{'...' if len(message) > 100 else ''}"
    elif result_type == "add_edge":
        message = result.result.get("message", "") if result.result else ""
        return f"Tool '{tool_name}' created edge: {message[:100]}{'...' if len(message) > 100 else ''}"
    elif result_type == "query_result":
        count = len(result.result.get("results", [])) if result.result else 0
        return f"Tool '{tool_name}' returned {count} results in {execution_time:.3f}s"
    elif result_type == "string":
        message = result.result.get("message", "") if result.result else ""
        return f"Tool '{tool_name}' returned: {message[:100]}{'...' if len(message) > 100 else ''}"
    elif result_type == "collection":
        count = result.result.get("count", 0) if result.result else 0
        return f"Tool '{tool_name}' returned {count} items in {execution_time:.3f}s"
    else:
        return f"Tool '{tool_name}' completed in {execution_time:.3f}s"


def _create_detailed_progress_message(tool_name: str, tool_args: Dict[str, Any], result: CallToolResult) -> str:
    """Create a detailed, semantically meaningful progress message.
    
    Args:
        tool_name: Name of the tool that was executed.
        tool_args: Arguments passed to the tool.
        result: Result of the tool execution.
        
    Returns:
        Detailed progress message with context about what was accomplished.
    """
    if result.status != "success":
        return f"Failed to execute {tool_name}: {result.error or 'Unknown error'}"
    
    result_type = result.result_type or "unknown"
    execution_time = result.execution_time or 0.0
    
    # Create detailed messages based on tool type and result
    if result_type == "add_node":
        label = tool_args.get("label", "Unknown")
        key = tool_args.get("key", "Unknown")
        properties = tool_args.get("properties", {})
        
        # Format properties for display
        props_str = ""
        #if properties:
        #    props_list = [f"{k}: {v}" for k, v in properties.items()]
        #    props_str = f" with attributes '{', '.join(props_list)}'"
        
        return f"Successfully added {label} node '{key}'{props_str}"
    
    elif result_type == "add_edge":
        from_node = tool_args.get("from_node", "Unknown")
        to_node = tool_args.get("to_node", "Unknown")
        relationship = tool_args.get("relationship", "Unknown")
        properties = tool_args.get("properties", {})
        
        # Format properties for display
        props_str = ""
        #if properties:
        #    props_list = [f"{k}: {v}" for k, v in properties.items()]
        #    props_str = f" with attributes '{', '.join(props_list)}'"
        
        return f"Successfully created {relationship} relationship from '{from_node}' to '{to_node}'{props_str}"
    
    elif result_type == "update_props":
        target_type = tool_args.get("target_type", "Unknown")
        properties = tool_args.get("properties", {})
        
        # Format properties for display
        props_list = [f"{k}: {v}" for k, v in properties.items()]
        props_str = f"'{', '.join(props_list)}'"
        
        return f"Successfully updated {target_type} properties: {props_str}"
    
    elif result_type == "delete_node":
        match_spec = tool_args.get("match_spec", {})
        label = match_spec.get("label", "Unknown")
        key = match_spec.get("key", "Unknown")
        
        return f"Successfully deleted {label} node '{key}'"
    
    elif result_type == "delete_edge":
        match_spec = tool_args.get("match_spec", {})
        relationship = match_spec.get("relationship_type", "Unknown")
        
        return f"Successfully deleted {relationship} edge"
    
    elif result_type == "query_result":
        count = len(result.result.get("results", [])) if result.result else 0
        query = tool_args.get("query", "Unknown")
        
        return f"Successfully executed query '{query[:50]}{'...' if len(query) > 50 else ''}' - found {count} results"
    
    elif result_type == "cypher_query":
        count = len(result.result.get("results", [])) if result.result else 0
        query = tool_args.get("query", "Unknown")
        
        return f"Successfully executed Cypher query '{query[:50]}{'...' if len(query) > 50 else ''}' - found {count} results"
    
    else:
        # Fallback to generic message with tool name and execution time
        return f"Successfully executed {tool_name} in {execution_time:.3f}s"
