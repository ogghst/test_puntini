"""Factory for creating context manager instances.

This module provides factory functions for creating different
types of context manager implementations.
"""

from typing import Any, Dict
from ..interfaces.context_manager import ContextManager


class ContextManagerConfig:
    """Configuration for context manager instances."""
    
    def __init__(self, kind: str, **kwargs: Any):
        """Initialize context manager configuration.
        
        Args:
            kind: Type of context manager ("progressive", "simple").
            **kwargs: Additional configuration parameters.
        """
        self.kind = kind
        self.config = kwargs


def make_context_manager(cfg: ContextManagerConfig) -> ContextManager:
    """Create a context manager instance based on configuration.
    
    Args:
        cfg: Context manager configuration.
        
    Returns:
        Configured context manager instance.
        
    Raises:
        ValueError: If the context manager type is not supported.
    """
    if cfg.kind == "progressive":
        # TODO: Implement progressive context manager
        from ..tools.context_manager import ProgressiveContextManager
        return ProgressiveContextManager(cfg.config)
    elif cfg.kind == "simple":
        from ..tools.context_manager import SimpleContextManager
        return SimpleContextManager(cfg.config)
    else:
        raise ValueError(f"Unsupported context manager type: {cfg.kind}")


def create_simple_context_manager() -> ContextManager:
    """Create a simple context manager for testing.
    
    Returns:
        Simple context manager instance.
    """
    cfg = ContextManagerConfig("simple")
    return make_context_manager(cfg)
