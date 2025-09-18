"""Route tool node implementation.

This module implements the route_tool node that selects the
appropriate tool or branch to ask/diagnose paths.
"""

from typing import Any, Dict, Optional, TYPE_CHECKING
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime

if TYPE_CHECKING:
    from ..orchestration.state_schema import State
from ..interfaces.tool_registry import ToolRegistry
from ..models.errors import ValidationError, NotFoundError
from ..logging import get_logger
from .message import RouteToolResponse, RouteToolResult, Artifact, ErrorContext

logger = get_logger(__name__)


def route_tool(
    state: "State", 
    config: Optional[RunnableConfig] = None, 
    runtime: Optional[Runtime] = None
) -> RouteToolResponse:
    """Route to the appropriate tool or branch.
    
    This node determines which tool to execute or which branch
    to take based on the planned step and current context. It validates
    the tool signature from the planning step and ensures the selected
    tool is available and appropriate for execution.
    
    Args:
        state: Current agent state with planned step.
        config: Optional RunnableConfig for additional configuration.
        runtime: Optional Runtime context for additional runtime information.
        
    Returns:
        Updated state with routing decision and validated tool information.
        
    Notes:
        Routing considers:
        - Tool availability in the registry
        - Tool signature validation
        - Current context and constraints
        - Fallback options for error scenarios
        
    Raises:
        ValidationError: If tool signature is invalid.
        NotFoundError: If specified tool is not available.
    """
    tool_signature = state.tool_signature or {}
    tool_name = tool_signature.get("tool_name")
    tool_args = tool_signature.get("tool_args", {})
    reasoning = tool_signature.get("reasoning", "No reasoning provided")
    confidence = tool_signature.get("confidence", 0.0)
    
    logger.debug(f"Routing tool: {tool_name} with args: {tool_args}")
    
    # Validate tool signature
    if not tool_name:
        error_msg = "No tool specified in tool signature"
        logger.error(error_msg)
        return RouteToolResponse(
            current_step="diagnose",
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
        return RouteToolResponse(
            current_step="diagnose",
            error_context=ErrorContext(
                type="system_error",
                message=error_msg,
                details={"component": "tool_registry", "solution": "Use create_initial_state() to initialize state with components"}
            )
        )
    
    # Check tool availability
    try:
        available_tools = [tool.name for tool in tool_registry.list()]
        if tool_name not in available_tools:
            error_msg = f"Tool '{tool_name}' not found in registry. Available tools: {available_tools}"
            logger.error(error_msg)
            return RouteToolResponse(
                current_step="diagnose",
                error_context=ErrorContext(
                    type="not_found_error",
                    message=error_msg,
                    details={
                        "requested_tool": tool_name,
                        "available_tools": available_tools
                    }
                )
            )
        
        # Get tool specification for validation
        tool_spec = None
        for tool in tool_registry.list():
            if tool.name == tool_name:
                tool_spec = tool
                break
        
        # Validate tool arguments against schema
        if tool_spec and tool_spec.input_schema:
            # Basic validation - check if required fields are present
            required_fields = tool_spec.input_schema.get("required", [])
            missing_fields = [field for field in required_fields if field not in tool_args]
            if missing_fields:
                error_msg = f"Missing required arguments for tool '{tool_name}': {missing_fields}"
                logger.error(error_msg)
                return RouteToolResponse(
                    current_step="diagnose",
                    error_context=ErrorContext(
                        type="validation_error",
                        message=error_msg,
                        details={
                            "tool_name": tool_name,
                            "missing_fields": missing_fields,
                            "provided_args": list(tool_args.keys())
                        }
                    )
                )
        
        # Create routing decision
        routing_decision = {
            "selected_tool": tool_name,
            "tool_args": tool_args,
            "routing_reason": reasoning,
            "confidence": confidence,
            "tool_available": True,
            "validation_passed": True,
            "fallback_available": len(available_tools) > 1
        }
        
        logger.info(f"Successfully routed to tool '{tool_name}' with confidence {confidence}")
        
        return RouteToolResponse(
            current_step="call_tool",
            tool_signature={
                **tool_signature,
                "validation_passed": True,
                "routing_decision": routing_decision
            },
            artifacts=[Artifact(type="routing_decision", data=routing_decision)],
            result=RouteToolResult(
                status="success",
                routing_decision=routing_decision
            )
        )
        
    except NotFoundError as e:
        error_msg = f"Tool not found: {str(e)}"
        logger.error(error_msg)
        return RouteToolResponse(
            current_step="diagnose",
            error_context=ErrorContext(
                type="not_found_error",
                message=error_msg,
                details={"tool_name": tool_name}
            )
        )
    except ValidationError as e:
        error_msg = f"Tool validation failed: {str(e)}"
        logger.error(error_msg)
        return RouteToolResponse(
            current_step="diagnose",
            error_context=ErrorContext(
                type="validation_error",
                message=error_msg,
                details={"tool_name": tool_name, "args": tool_args}
            )
        )
    except Exception as e:
        error_msg = f"Unexpected error during tool routing: {str(e)}"
        logger.error(error_msg)
        return RouteToolResponse(
            current_step="diagnose",
            error_context=ErrorContext(
                type="system_error",
                message=error_msg,
                details={"tool_name": tool_name}
            )
        )
