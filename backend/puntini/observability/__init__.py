"""Observability and tracing module for the Puntini Agent.

This module provides comprehensive observability capabilities including
tracing, monitoring, and logging for the agent's execution. It supports
multiple backends including Langfuse, console output, and no-op implementations.
"""

from .tracer_factory import (
    create_langfuse_tracer,
    create_noop_tracer,
    create_console_tracer,
    make_tracer,
    TracerConfig,
)
from .langfuse_tracer import LangfuseTracer
from .console_tracer import ConsoleTracer
from .noop_tracer import NoOpTracer
from .langfuse_callback import LangfuseCallbackHandler

__all__ = [
    # Factory functions
    "create_langfuse_tracer",
    "create_noop_tracer",
    "create_console_tracer",
    "make_tracer",
    "TracerConfig",
    
    # Tracer implementations
    "LangfuseTracer",
    "ConsoleTracer", 
    "NoOpTracer",
    
    # Callback handlers
    "LangfuseCallbackHandler",
]
