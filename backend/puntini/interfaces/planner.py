"""Planner interface for agent step planning.

This module defines the Planner protocol that handles the planning of
individual steps in the agent's execution flow.
"""

from typing import Any, Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from ..orchestration.state_schema import State


class Planner(Protocol):
    """Protocol for planning agent execution steps.
    
    The planner is responsible for determining the next step in the agent's
    execution flow based on the current state and available tools.
    """
    
    def plan_next_step(self, state: "State") -> dict[str, Any]:
        """Plan the next step in the agent's execution.

        Args:
            state: Current agent state.

        Returns:
            Dictionary containing the planned step with tool signature and parameters.

        Raises:
            PlanningError: If planning fails due to invalid state or constraints.

        Notes:
            The returned step should include all necessary information for
            tool execution, including the tool name and validated parameters.
        """
        ...
    
    def validate_step(self, step: dict[str, Any]) -> bool:
        """Validate a planned step before execution.

        Args:
            step: Planned step to validate.

        Returns:
            True if the step is valid, False otherwise.

        Notes:
            Validation should check tool availability, parameter types,
            and any constraints that must be satisfied.
        """
        ...