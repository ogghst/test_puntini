"""Puntini Agent - A controllable, observable multi-tool agent for graph manipulation.

This package provides a stateful agent that translates natural language into
safe, idempotent graph operations and graph-aware answers using LangGraph
and LangChain with progressive context disclosure and production-grade
instrumentation via Langfuse.
"""

from .agents.agent_factory import create_simple_agent, create_agent_with_components
from .graph.graph_store_factory import create_memory_graph_store
from .context.context_manager_factory import create_simple_context_manager
from .tools.tool_registry_factory import create_standard_tool_registry
from .observability.tracer_factory import create_langfuse_tracer, create_noop_tracer
from .orchestration.graph import create_agent_graph, create_agent_with_checkpointer
from .settings import settings

__version__ = "0.1.0"
__author__ = "Puntini Agent Team"
__description__ = "A controllable, observable multi-tool agent for graph manipulation"

__all__ = [
    "create_simple_agent",
    "create_agent_with_components",
    "create_memory_graph_store",
    "create_simple_context_manager",
    "create_standard_tool_registry",
    "create_langfuse_tracer",
    "create_noop_tracer",
    "create_agent_graph",
    "create_agent_with_checkpointer",
    "settings",
]
