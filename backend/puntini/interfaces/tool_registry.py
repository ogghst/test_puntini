"""Tool registry interface for managing agent tools.

This module defines the ToolRegistry protocol that manages tool registration,
retrieval, and schema validation for the agent's tool ecosystem.
"""

from typing import Any, Callable, Protocol
from ..models.specs import ToolSpec


class ToolCallable(Protocol):
    """Protocol for callable tools.
    
    Tools must be callable and return structured results that can be
    processed by the agent's execution pipeline.
    """
    
    def __call__(self, **kwargs: Any) -> Any:
        """Execute the tool with the given arguments.

        Args:
            **kwargs: Tool arguments as keyword arguments.

        Returns:
            Tool execution result.

        Raises:
            ToolError: If tool execution fails.
            ValidationError: If arguments are not valid.

        Notes:
            Tools should be pure functions when possible and handle
            their own error cases gracefully.
        """
        ...


class ToolRegistry(Protocol):
    """Protocol for managing agent tools and their schemas.
    
    The tool registry provides a centralized way to register, retrieve,
    and manage tools with their associated schemas for structured tool calling.
    """
    
    def register(self, tool: ToolSpec) -> None:
        """Register a new tool with its specification.

        Args:
            tool: Tool specification containing name, description, schema, and callable.

        Raises:
            ValidationError: If the tool specification is not valid.
            DuplicateError: If a tool with the same name is already registered.

        Notes:
            Tool registration should validate the schema and ensure the
            callable is compatible with the specified signature.
        """
        ...
    
    def get(self, name: str) -> ToolCallable:
        """Retrieve a tool by name.

        Args:
            name: Name of the tool to retrieve.

        Returns:
            The callable tool.

        Raises:
            NotFoundError: If no tool with the given name is registered.

        Notes:
            The returned tool should be ready for immediate execution
            with validated arguments.
        """
        ...
    
    def list(self) -> list[ToolSpec]:
        """List all registered tools.

        Returns:
            List of all registered tool specifications.

        Notes:
            The returned list should be a copy to prevent external
            modification of the registry's internal state.
        """
        ...