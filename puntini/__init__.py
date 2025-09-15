"""Puntini Agent - A controllable, observable multi-tool agent for graph manipulation.

This package provides a stateful agent that translates natural language into
safe, idempotent graph operations and graph-aware answers using LangGraph
and LangChain with progressive context disclosure and production-grade
instrumentation via Langfuse.

The agent follows a modular architecture with clear separation of concerns:
- Graph operations with idempotent semantics
- Progressive context disclosure for LLM interactions
- Comprehensive observability and tracing
- Structured error handling and recovery
- Human-in-the-loop escalation capabilities

Example:
    >>> from puntini import create_simple_agent, create_initial_state
    >>> agent = create_simple_agent()
    >>> state = create_initial_state("Create a user node", ...)
    >>> result = agent.invoke(state)
"""

# Core agent functionality
from .agents.agent_factory import (
    create_simple_agent,
    create_agent_with_components,
    create_initial_state,
    AgentConfig,
)

# Graph store implementations
from .graph.graph_store_factory import (
    create_memory_graph_store,
    GraphStoreConfig,
)

# Context management
from .context.context_manager_factory import (
    create_simple_context_manager,
    ContextManagerConfig,
)

# Tool registry
from .tools.tool_registry_factory import (
    create_standard_tool_registry,
    ToolRegistryConfig,
)

# Observability and tracing
from .observability.tracer_factory import (
    create_langfuse_tracer,
    create_noop_tracer,
    create_console_tracer,
    TracerConfig,
)

# Graph orchestration
from .orchestration.graph import (
    create_agent_graph,
    create_agent_with_checkpointer,
)

# Interfaces
from .interfaces import (
    GraphStore,
    ContextManager,
    ToolRegistry,
    Tracer,
    Planner,
    Executor,
    Evaluator,
    ErrorClassifier,
    EscalationHandler,
    ModelInput,
    ToolCallable,
)

# Settings and configuration
from .utils.settings import (
    Settings,
    LLMConfig,
    LLMProviderConfig,
    LoggingConfig,
    AgentConfig as SettingsAgentConfig,
)

# Core data models
from .models.base import BaseEntity
from .models.node import Node
from .models.edge import Edge
from .models.specs import NodeSpec, EdgeSpec, MatchSpec, ToolSpec
from .models.errors import (
    AgentError,
    ValidationError,
    ConstraintViolationError,
    NotFoundError,
    ToolError,
)

# Logging utilities
from .logging import (
    get_logger,
    setup_logging,
    get_logging_service,
)

# LLM factory
from .llm.llm_models import LLMFactory

# Package metadata
__version__ = "0.1.0"
__author__ = "Puntini Agent Team"
__description__ = "A controllable, observable multi-tool agent for graph manipulation"
__license__ = "MIT"
__url__ = "https://github.com/puntini-agent/puntini"

# Public API exports
__all__ = [
    # Core agent functionality
    "create_simple_agent",
    "create_agent_with_components", 
    "create_initial_state",
    "AgentConfig",
    
    # Graph operations
    "create_memory_graph_store",
    "GraphStoreConfig",
    
    # Context management
    "create_simple_context_manager",
    "ContextManagerConfig",
    
    # Tool registry
    "create_standard_tool_registry",
    "ToolRegistryConfig",
    
    # Observability
    "create_langfuse_tracer",
    "create_noop_tracer",
    "create_console_tracer",
    "TracerConfig",
    
    # Graph orchestration
    "create_agent_graph",
    "create_agent_with_checkpointer",
    
    # Interfaces
    "GraphStore",
    "ContextManager",
    "ToolRegistry",
    "Tracer",
    "Planner",
    "Executor",
    "Evaluator",
    "ErrorClassifier",
    "EscalationHandler",
    "ModelInput",
    "ToolCallable",
    
    # Settings and configuration
    "Settings",
    "LLMConfig",
    "LLMProviderConfig", 
    "LoggingConfig",
    "SettingsAgentConfig",
    
    # Core data models
    "BaseEntity",
    "Node",
    "Edge",
    "NodeSpec",
    "EdgeSpec", 
    "MatchSpec",
    "ToolSpec",
    
    # Error classes
    "AgentError",
    "ValidationError",
    "ConstraintViolationError",
    "NotFoundError",
    "ToolError",
    
    # Logging
    "get_logger",
    "setup_logging",
    "get_logging_service",
    
    # LLM factory
    "LLMFactory",
]
