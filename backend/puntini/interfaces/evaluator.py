"""Evaluator interface for step evaluation and routing.

This module defines the Evaluator protocol that handles the evaluation
of step results and routing decisions for the agent's state machine.
"""

from typing import Any, Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from ..orchestration.state_schema import State


class Evaluator(Protocol):
    """Protocol for evaluating step results and making routing decisions.
    
    The evaluator is responsible for determining whether to advance,
    retry, or diagnose based on the current state and step results.
    """
    
    def evaluate_step(self, state: "State", result: dict[str, Any]) -> str:
        """Evaluate a step result and determine the next action.

        Args:
            state: Current agent state.
            result: Result from the executed step.

        Returns:
            Next action: "advance", "retry", or "diagnose".

        Notes:
            The evaluator should consider the current state, step results,
            and failure patterns to make routing decisions.
        """
        ...
    
    def should_retry(self, state: "State", error: dict[str, Any]) -> bool:
        """Determine if a step should be retried.

        Args:
            state: Current agent state.
            error: Error information from the failed step.

        Returns:
            True if the step should be retried, False otherwise.

        Notes:
            Retry decisions should consider retry limits, error types,
            and the current attempt count.
        """
        ...
    
    def should_escalate(self, state: "State") -> bool:
        """Determine if the agent should escalate to human input.

        Args:
            state: Current agent state.

        Returns:
            True if escalation is needed, False otherwise.

        Notes:
            Escalation should be triggered when retry limits are exceeded
            or when human intervention is required for decision making.
        """
        ...

