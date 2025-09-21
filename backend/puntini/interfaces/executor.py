"""Executor interface for tool execution.

This module defines the Executor protocol that handles the execution
of tools and normalization of their results.
"""

from typing import Any, Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from ..orchestration.state_schema import State


class Executor(Protocol):
    """Protocol for executing agent tools.
    
    The executor is responsible for executing tools with validated inputs
    and normalizing their results for consumption by the agent.
    """
    
    def execute_tool(self, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
        """Execute a tool with the given arguments.

        Args:
            tool_name: Name of the tool to execute.
            args: Tool arguments as a dictionary.

        Returns:
            Dictionary containing the tool execution result.

        Raises:
            ToolError: If tool execution fails.
            ValidationError: If arguments are not valid.

        Notes:
            The executor should handle tool errors gracefully and return
            normalized, human-readable error messages when possible.
        """
        ...
    
    def normalize_result(self, result: Any) -> dict[str, Any]:
        """Normalize a tool execution result.

        Args:
            result: Raw tool execution result.

        Returns:
            Normalized result dictionary.

        Notes:
            Normalization ensures consistent result format across all tools
            and handles any tool-specific result formatting.
        """
        ...