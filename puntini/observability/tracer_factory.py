"""Factory for creating tracer instances.

This module provides factory functions for creating different
types of tracer implementations for observability.
"""

from typing import Any, Dict
from ..interfaces.tracer import Tracer


class TracerConfig:
    """Configuration for tracer instances."""
    
    def __init__(self, kind: str, **kwargs: Any):
        """Initialize tracer configuration.
        
        Args:
            kind: Type of tracer ("langfuse", "noop", "console").
            **kwargs: Additional configuration parameters.
        """
        self.kind = kind
        self.config = kwargs


def make_tracer(cfg: TracerConfig) -> Tracer:
    """Create a tracer instance based on configuration.
    
    Args:
        cfg: Tracer configuration.
        
    Returns:
        Configured tracer instance.
        
    Raises:
        ValueError: If the tracer type is not supported.
    """
    if cfg.kind == "langfuse":
        from ..observability.langfuse_tracer import LangfuseTracer
        return LangfuseTracer(cfg.config)
    elif cfg.kind == "noop":
        from ..observability.noop_tracer import NoOpTracer
        return NoOpTracer()
    elif cfg.kind == "console":
        from ..observability.console_tracer import ConsoleTracer
        return ConsoleTracer(cfg.config)
    else:
        raise ValueError(f"Unsupported tracer type: {cfg.kind}")


def create_noop_tracer() -> Tracer:
    """Create a no-op tracer for testing.
    
    Returns:
        No-op tracer instance.
    """
    cfg = TracerConfig("noop")
    return make_tracer(cfg)


def create_console_tracer() -> Tracer:
    """Create a console tracer for development.
    
    Returns:
        Console tracer instance.
    """
    cfg = TracerConfig("console")
    return make_tracer(cfg)
