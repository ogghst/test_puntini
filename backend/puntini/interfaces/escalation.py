"""Escalation handler interface for human-in-the-loop interactions.

This module defines the EscalationHandler protocol that handles escalation
to human input and manages the human-in-the-loop workflow.
"""

from typing import Any, Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from ..orchestration.state_schema import State


class EscalationHandler(Protocol):
    """Protocol for handling escalation to human input.
    
    The escalation handler manages the human-in-the-loop workflow,
    including interrupt handling and resume capabilities.
    """
    
    def should_escalate(self, state: "State") -> bool:
        """Determine if escalation to human input is needed.

        Args:
            state: Current agent state.

        Returns:
            True if escalation is needed, False otherwise.

        Notes:
            Escalation should be triggered when retry limits are exceeded,
            when human decision-making is required, or when the agent
            encounters an unrecoverable error.
        """
        ...
    
    def prepare_escalation_context(self, state: "State") -> dict[str, Any]:
        """Prepare context for human escalation.

        Args:
            state: Current agent state.

        Returns:
            Dictionary containing escalation context and options.

        Notes:
            The escalation context should include a clear summary of the
            current situation, available options, and recommended actions.
        """
        ...
    
    def handle_human_input(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Process human input and return updated state.

        Args:
            input_data: Human input data.

        Returns:
            Updated state based on human input.

        Raises:
            ValidationError: If human input is not valid.
            EscalationError: If human input cannot be processed.

        Notes:
            Human input should be validated and processed to update the
            agent state appropriately for resuming execution.
        """
        ...
    
    def resume_after_escalation(self, state: "State") -> "State":
        """Resume agent execution after human escalation.

        Args:
            state: Current agent state after human input.

        Returns:
            Updated state ready for resuming execution.

        Notes:
            This method should clean up escalation-specific state and
            prepare the agent for normal execution flow.
        """
        ...

