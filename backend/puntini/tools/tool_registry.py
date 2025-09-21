"""Tool registry implementations.

This module provides implementations of the ToolRegistry interface
for managing agent tools and their schemas.
"""

from typing import Any, Dict, List
from ..interfaces.tool_registry import ToolCallable, ToolRegistry
from ..models.specs import ToolSpec
from ..models.errors import ValidationError, NotFoundError, DuplicateError


class StandardToolRegistry:
    """Standard implementation of ToolRegistry.
    
    This implementation provides basic tool registration and retrieval
    functionality with schema validation.
    """
    
    def __init__(self, config: Dict[str, Any] | None = None):
        """Initialize the tool registry.
        
        Args:
            config: Optional configuration dictionary.
        """
        self._tools: Dict[str, ToolSpec] = {}
        self._config = config or {}
    
    def register(self, tool: ToolSpec) -> None:
        """Register a new tool with its specification.

        Args:
            tool: Tool specification containing name, description, schema, and callable.

        Raises:
            ValidationError: If the tool specification is not valid.
            DuplicateError: If a tool with the same name is already registered.
        """
        if not tool.name or not tool.description:
            raise ValidationError("Tool name and description are required")
        
        if not callable(tool.callable):
            raise ValidationError("Tool callable must be callable")
        
        if tool.name in self._tools:
            raise DuplicateError(f"Tool '{tool.name}' is already registered")
        
        self._tools[tool.name] = tool
    
    def get(self, name: str) -> ToolCallable:
        """Retrieve a tool by name.

        Args:
            name: Name of the tool to retrieve.

        Returns:
            The callable tool.

        Raises:
            NotFoundError: If no tool with the given name is registered.
        """
        if name not in self._tools:
            raise NotFoundError(f"Tool '{name}' not found")
        
        return self._tools[name].callable
    
    def list(self) -> List[ToolSpec]:
        """List all registered tools.

        Returns:
            List of all registered tool specifications.
        """
        return list(self._tools.values())


class CachedToolRegistry(StandardToolRegistry):
    """Cached implementation of ToolRegistry.
    
    This implementation adds caching for tool retrieval and
    schema validation results.
    """
    
    def __init__(self, config: Dict[str, Any] | None = None):
        """Initialize the cached tool registry.
        
        Args:
            config: Optional configuration dictionary.
        """
        super().__init__(config)
        self._callable_cache: Dict[str, ToolCallable] = {}
        self._schema_cache: Dict[str, Dict[str, Any]] = {}
    
    def get(self, name: str) -> ToolCallable:
        """Retrieve a tool by name with caching.

        Args:
            name: Name of the tool to retrieve.

        Returns:
            The callable tool.

        Raises:
            NotFoundError: If no tool with the given name is registered.
        """
        if name in self._callable_cache:
            return self._callable_cache[name]
        
        callable_tool = super().get(name)
        self._callable_cache[name] = callable_tool
        return callable_tool
