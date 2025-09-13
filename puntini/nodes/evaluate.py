"""Evaluate node implementation.

This module implements the evaluate node that decides advance,
retry, or diagnose based on step results.
"""

from typing import Any, Dict
from langgraph.types import Command
from ..orchestration.state import State


def evaluate(state: State) -> Dict[str, Any]:
    """Evaluate the step result and decide next action.
    
    This node analyzes the result of the executed step and determines
    whether to advance, retry, or diagnose based on the outcome.
    The routing decision is handled by conditional edges in the graph.
    
    Args:
        state: Current agent state with step result.
        
    Returns:
        A dictionary with the updated state. The graph will not use a Command here,
        but the router function `route_after_evaluate` will inspect the state.
        
    Notes:
        The evaluation should consider the step result, current retry
        count, and any error patterns. The actual routing is handled
        by conditional edges using the routing functions.
    """
    result = state.get("result", {})
    status = result.get("status", "unknown")
    retry_count = state.get("retry_count", 0)
    
    if status == "success":
        # The 'goal_complete' flag should be set by the tool if the goal is met.
        goal_complete = result.get("goal_complete", False)
        return {
            "result": {
                "status": "success",
                "goal_complete": goal_complete
            }
        }
    else: # status == "error"
        return {
            "retry_count": retry_count + 1,
            "result": {
                "status": "error"
            }
        }
