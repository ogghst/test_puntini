"""Context manager implementations.

This module provides implementations of the ContextManager interface
for managing context preparation and progressive disclosure.
"""

from typing import Any, Dict, List
from ..interfaces.context_manager import ContextManager, ModelInput
from ..orchestration.state import State


class SimpleContextManager:
    """Simple implementation of ContextManager.
    
    This implementation provides basic context management without
    progressive disclosure features.
    """
    
    def __init__(self, config: Dict[str, Any] | None = None):
        """Initialize the context manager.
        
        Args:
            config: Optional configuration dictionary.
        """
        self._config = config or {}
    
    def prepare_minimal_context(self, state: State) -> ModelInput:
        """Prepare minimal context for the first attempt.

        Args:
            state: Current agent state.

        Returns:
            ModelInput containing only the current task and minimal tool signatures.
        """
        return {
            "goal": state.get("goal", ""),
            "current_step": state.get("current_step", ""),
            "available_tools": ["add_node", "add_edge", "cypher_qa"]
        }
    
    def add_error_context(self, state: State, error: Dict[str, Any]) -> ModelInput:
        """Add error context for the second attempt.

        Args:
            state: Current agent state.
            error: Structured error information from the previous attempt.

        Returns:
            ModelInput with error context and just-enough payload to disambiguate.
        """
        base_context = self.prepare_minimal_context(state)
        base_context["error"] = error
        base_context["retry_count"] = state.get("retry_count", 0)
        return base_context
    
    def add_historical_context(self, state: State) -> ModelInput:
        """Add historical context for the third attempt.

        Args:
            state: Current agent state.

        Returns:
            ModelInput with selected history and concise plan recap.
        """
        base_context = self.prepare_minimal_context(state)
        base_context["progress"] = state.get("progress", [])
        base_context["failures"] = state.get("failures", [])
        return base_context
    
    def record_failure(self, state: State, error: Dict[str, Any]) -> State:
        """Record a failure in the agent state.

        Args:
            state: Current agent state.
            error: Structured error information.

        Returns:
            Updated state with failure recorded.
        """
        failures = state.get("failures", [])
        failures.append(error)
        return {**state, "failures": failures}
    
    def advance_step(self, state: State, result: Dict[str, Any]) -> State:
        """Advance to the next step in the agent's execution.

        Args:
            state: Current agent state.
            result: Result from the current step.

        Returns:
            Updated state with progress recorded.
        """
        progress = state.get("progress", [])
        progress.append(f"Step completed: {result.get('status', 'unknown')}")
        return {**state, "progress": progress}
    
    def is_complete(self, state: State) -> bool:
        """Check if the agent's goal has been completed.

        Args:
            state: Current agent state.

        Returns:
            True if the goal is complete, False otherwise.
        """
        return state.get("current_step") == "complete"


class ProgressiveContextManager(SimpleContextManager):
    """Progressive implementation of ContextManager.
    
    This implementation provides progressive context disclosure
    with multiple levels of context detail.
    """
    
    def __init__(self, config: Dict[str, Any] | None = None):
        """Initialize the progressive context manager.
        
        Args:
            config: Optional configuration dictionary.
        """
        super().__init__(config)
        self._max_attempts = config.get("max_attempts", 3)
        self._disclosure_levels = config.get("disclosure_levels", ["minimal", "error", "historical"])
    
    def prepare_minimal_context(self, state: State) -> ModelInput:
        """Prepare minimal context for the first attempt.

        Args:
            state: Current agent state.

        Returns:
            ModelInput containing only the current task and minimal tool signatures.
        """
        context = super().prepare_minimal_context(state)
        context["disclosure_level"] = "minimal"
        context["attempt"] = 1
        return context
    
    def add_error_context(self, state: State, error: Dict[str, Any]) -> ModelInput:
        """Add error context for the second attempt.

        Args:
            state: Current agent state.
            error: Structured error information from the previous attempt.

        Returns:
            ModelInput with error context and just-enough payload to disambiguate.
        """
        context = super().add_error_context(state, error)
        context["disclosure_level"] = "error"
        context["attempt"] = 2
        return context
    
    def add_historical_context(self, state: State) -> ModelInput:
        """Add historical context for the third attempt.

        Args:
            state: Current agent state.

        Returns:
            ModelInput with selected history and concise plan recap.
        """
        context = super().add_historical_context(state)
        context["disclosure_level"] = "historical"
        context["attempt"] = 3
        return context
