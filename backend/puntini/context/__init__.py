"""Context management module for progressive disclosure.

This module provides context manager implementations that handle
progressive context disclosure strategies for the agent's state management.
It supports both simple and progressive context management approaches.
"""

from .context_manager import (
    SimpleContextManager,
    ProgressiveContextManager,
)
from .context_manager_factory import (
    create_simple_context_manager,
    make_context_manager,
    ContextManagerConfig,
)
from .graph_context import (
    GraphContextManager,
    ContextAwareEntityMatcher,
    GraphSubgraph,
    SubgraphQuery
)

__all__ = [
    "SimpleContextManager",
    "ProgressiveContextManager",
    "create_simple_context_manager",
    "make_context_manager", 
    "ContextManagerConfig",
    "GraphContextManager",
    "ContextAwareEntityMatcher",
    "GraphSubgraph",
    "SubgraphQuery"
]
