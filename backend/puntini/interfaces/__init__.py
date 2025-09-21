"""Interface definitions for the Puntini Agent system.

This package contains all the protocol definitions and interfaces that define
the contracts for the various components of the agent system. These interfaces
ensure consistent behavior across different implementations and enable easy
testing and mocking.
"""

from .context_manager import ContextManager, ModelInput
from .error_classifier import ErrorClassifier
from .escalation import EscalationHandler
from .evaluator import Evaluator
from .executor import Executor
from .graph_store import GraphStore
from .planner import Planner
from .tool_registry import ToolRegistry, ToolCallable
from .tracer import Tracer

__all__ = [
    # Core interfaces
    "GraphStore",
    "ContextManager", 
    "ToolRegistry",
    "Tracer",
    
    # Agent workflow interfaces
    "Planner",
    "Executor",
    "Evaluator",
    "ErrorClassifier",
    "EscalationHandler",
    
    # Supporting types
    "ModelInput",
    "ToolCallable",
]