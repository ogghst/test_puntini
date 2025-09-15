"""Factory for creating tool registry instances.

This module provides factory functions for creating different
types of tool registry implementations.
"""

from typing import Any, Dict
from ..interfaces.tool_registry import ToolRegistry


class ToolRegistryConfig:
    """Configuration for tool registry instances."""
    
    def __init__(self, kind: str, **kwargs: Any):
        """Initialize tool registry configuration.
        
        Args:
            kind: Type of tool registry ("standard", "cached").
            **kwargs: Additional configuration parameters.
        """
        self.kind = kind
        self.config = kwargs


def make_tool_registry(cfg: ToolRegistryConfig) -> ToolRegistry:
    """Create a tool registry instance based on configuration.
    
    Args:
        cfg: Tool registry configuration.
        
    Returns:
        Configured tool registry instance.
        
    Raises:
        ValueError: If the tool registry type is not supported.
    """
    if cfg.kind == "standard":
        from ..tools.tool_registry import StandardToolRegistry
        return StandardToolRegistry(cfg.config)
    elif cfg.kind == "cached":
        from ..tools.tool_registry import CachedToolRegistry
        return CachedToolRegistry(cfg.config)
    else:
        raise ValueError(f"Unsupported tool registry type: {cfg.kind}")


def create_standard_tool_registry() -> ToolRegistry:
    """Create a standard tool registry for testing.
    
    Returns:
        Standard tool registry instance.
    """
    cfg = ToolRegistryConfig("standard")
    return make_tool_registry(cfg)
