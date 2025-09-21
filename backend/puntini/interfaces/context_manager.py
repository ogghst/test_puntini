"""Context manager interface for progressive context disclosure.

This module defines the ContextManager protocol that manages context preparation
and progressive disclosure strategies for the agent's state management.
"""

from typing import Any, Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from ..orchestration.state_schema import State


class ModelInput(Protocol):
    """Protocol for model input data structure.
    
    This represents the prepared input that will be sent to the LLM,
    containing the appropriate context based on the current disclosure level.
    """
    pass


class ContextManager(Protocol):
    """Protocol for managing context preparation and progressive disclosure.
    
    The context manager implements a progressive disclosure strategy that
    gradually increases the amount of context provided to the LLM based on
    the current attempt and failure patterns.
    """
    
    def prepare_minimal_context(self, state: "State") -> ModelInput:
        """Prepare minimal context for the first attempt.

        Args:
            state: Current agent state.

        Returns:
            ModelInput containing only the current task and minimal tool signatures.

        Notes:
            This is the first level of context disclosure, providing only
            essential information to avoid overwhelming the LLM.
        """
        ...
    
    def add_error_context(self, state: "State", error: dict) -> ModelInput:
        """Add error context for the second attempt.

        Args:
            state: Current agent state.
            error: Structured error information from the previous attempt.

        Returns:
            ModelInput with error context and just-enough payload to disambiguate.

        Notes:
            This is the second level of context disclosure, adding error
            information to help the LLM understand what went wrong.
        """
        ...
    
    def add_historical_context(self, state: "State") -> ModelInput:
        """Add historical context for the third attempt.

        Args:
            state: Current agent state.

        Returns:
            ModelInput with selected history and concise plan recap.

        Notes:
            This is the third level of context disclosure, providing
            historical context to help the LLM understand the full context.
        """
        ...
    
    def record_failure(self, state: "State", error: dict) -> "State":
        """Record a failure in the agent state.

        Args:
            state: Current agent state.
            error: Structured error information.

        Returns:
            Updated state with failure recorded.

        Notes:
            Failures are tracked to implement retry policies and escalation
            thresholds. The state should be updated atomically.
        """
        ...
    
    def advance_step(self, state: "State", result: dict) -> "State":
        """Advance to the next step in the agent's execution.

        Args:
            state: Current agent state.
            result: Result from the current step.

        Returns:
            Updated state with progress recorded.

        Notes:
            This method updates the progress tracking and prepares the state
            for the next step in the execution flow.
        """
        ...
    
    def is_complete(self, state: "State") -> bool:
        """Check if the agent's goal has been completed.

        Args:
            state: Current agent state.

        Returns:
            True if the goal is complete, False otherwise.

        Notes:
            This method implements the completion criteria for the agent's
            goal. It should be deterministic and based on the current state.
        """
        ...