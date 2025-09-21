"""Tool setup utilities for the agent.

This module provides functions to set up and register all tools
in the tool registry with proper type checking and validation.
"""

from typing import List, Any
from langchain_core.tools import BaseTool

from .tool_registry import StandardToolRegistry
from .tool_registry_factory import ToolRegistryConfig, make_tool_registry
from .graph_tools import GRAPH_TOOLS
from ..models.specs import ToolSpec
from ..interfaces.tool_registry import ToolRegistry


def create_tool_spec_from_langchain_tool(tool: BaseTool) -> ToolSpec:
    """Convert a LangChain tool to a ToolSpec.
    
    Args:
        tool: LangChain BaseTool instance.
        
    Returns:
        ToolSpec object with tool information.
        
    Raises:
        ValueError: If tool is not a valid LangChain tool.
    """
    if not isinstance(tool, BaseTool):
        raise ValueError(f"Tool must be a LangChain BaseTool, got {type(tool)}")
    
    return ToolSpec(
        name=tool.name,
        description=tool.description,
        input_schema=tool.args_schema.model_json_schema() if tool.args_schema else {},
        callable=tool
    )


def register_graph_tools(tool_registry: ToolRegistry) -> None:
    """Register all graph manipulation tools in the tool registry.
    
    Args:
        tool_registry: Tool registry instance to register tools with.
        
    Raises:
        ValidationError: If tool registration fails.
        DuplicateError: If a tool with the same name is already registered.
    """
    for tool in GRAPH_TOOLS:
        try:
            tool_spec = create_tool_spec_from_langchain_tool(tool)
            tool_registry.register(tool_spec)
        except Exception as e:
            raise ValueError(f"Failed to register tool {tool.name}: {str(e)}")


def create_configured_tool_registry() -> ToolRegistry:
    """Create a tool registry with all graph tools pre-registered.
    
    Returns:
        Configured tool registry with all tools registered.
        
    Raises:
        ValueError: If tool registration fails.
    """
    # Create tool registry
    config = ToolRegistryConfig("standard")
    tool_registry = make_tool_registry(config)
    
    # Register all graph tools
    register_graph_tools(tool_registry)
    
    return tool_registry


def get_available_tools(tool_registry: ToolRegistry) -> List[str]:
    """Get list of available tool names from the registry.
    
    Args:
        tool_registry: Tool registry instance.
        
    Returns:
        List of tool names.
    """
    return [tool.name for tool in tool_registry.list()]


def validate_tool_registry(tool_registry: ToolRegistry) -> bool:
    """Validate that the tool registry is properly configured.
    
    Args:
        tool_registry: Tool registry instance to validate.
        
    Returns:
        True if valid, False otherwise.
    """
    try:
        # Check if registry has tools
        tools = tool_registry.list()
        if not tools:
            return False
        
        # Check if all expected tools are present
        expected_tools = {tool.name for tool in GRAPH_TOOLS}
        available_tools = {tool.name for tool in tools}
        
        return expected_tools.issubset(available_tools)
    except Exception:
        return False


def create_tool_registry_with_validation() -> ToolRegistry:
    """Create and validate a tool registry with all tools.
    
    Returns:
        Validated tool registry instance.
        
    Raises:
        ValueError: If tool registry creation or validation fails.
    """
    tool_registry = create_configured_tool_registry()
    
    if not validate_tool_registry(tool_registry):
        raise ValueError("Tool registry validation failed")
    
    return tool_registry
