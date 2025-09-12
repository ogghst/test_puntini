"""Factory for creating agent instances.

This module provides factory functions for creating the main
agent with all its dependencies configured.
"""

from typing import Any, Dict
from langgraph.graph import StateGraph
from ..orchestration.graph import create_agent_graph, create_agent_with_checkpointer
from ..interfaces.graph_store import GraphStore
from ..interfaces.context_manager import ContextManager
from ..interfaces.tool_registry import ToolRegistry
from ..interfaces.tracer import Tracer


class AgentConfig:
    """Configuration for agent instances."""
    
    def __init__(self, **kwargs: Any):
        """Initialize agent configuration.
        
        Args:
            **kwargs: Configuration parameters including:
                - graph_store: Graph store configuration
                - context_manager: Context manager configuration
                - tool_registry: Tool registry configuration
                - tracer: Tracer configuration
                - checkpointer: Checkpointer configuration
        """
        self.graph_store = kwargs.get("graph_store", {})
        self.context_manager = kwargs.get("context_manager", {})
        self.tool_registry = kwargs.get("tool_registry", {})
        self.tracer = kwargs.get("tracer", {})
        self.checkpointer = kwargs.get("checkpointer", {})


def make_agent(cfg: AgentConfig) -> StateGraph:
    """Create an agent instance with all dependencies configured.
    
    Args:
        cfg: Agent configuration.
        
    Returns:
        Compiled LangGraph state machine.
        
    Notes:
        This function creates all the necessary components and
        assembles them into a working agent.
    """
    # Create checkpointer if specified
    checkpointer = None
    if cfg.checkpointer:
        from ..orchestration.checkpointer import create_checkpointer
        checkpointer = create_checkpointer(**cfg.checkpointer)
    
    # Create the agent graph
    if checkpointer:
        return create_agent_with_checkpointer(**cfg.checkpointer)
    else:
        return create_agent_graph()


def create_simple_agent() -> StateGraph:
    """Create a simple agent for testing.
    
    Returns:
        Simple agent instance with minimal configuration.
    """
    cfg = AgentConfig(
        checkpointer={"checkpointer_type": "memory"}
    )
    return make_agent(cfg)


def create_agent_with_components(
    graph_store: GraphStore,
    context_manager: ContextManager,
    tool_registry: ToolRegistry,
    tracer: Tracer
) -> StateGraph:
    """Create an agent with pre-configured components.
    
    Args:
        graph_store: Configured graph store instance.
        context_manager: Configured context manager instance.
        tool_registry: Configured tool registry instance.
        tracer: Configured tracer instance.
        
    Returns:
        Compiled LangGraph state machine with components.
        
    Notes:
        This function allows for more control over component
        configuration and is useful for testing and advanced use cases.
    """
    # TODO: Wire components into the agent
    # This is a placeholder implementation
    cfg = AgentConfig()
    return make_agent(cfg)
