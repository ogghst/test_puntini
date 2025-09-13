"""Evaluate node implementation.

This module implements the evaluate node that decides advance,
retry, or diagnose based on step results.
"""

from typing import Any, Dict
from ..orchestration.state import State


def evaluate(state: State) -> Dict[str, Any]:
    """Evaluate the step result and decide next action.
    
    This node analyzes the result of the executed step and determines
    whether to advance, retry, or diagnose based on the outcome.
    The routing decision is handled by conditional edges in the graph.
    
    Args:
        state: Current agent state with step result.
        
    Returns:
        Updated state with evaluation results.
        
    Notes:
        The evaluation should consider the step result, current retry
        count, and any error patterns. The actual routing is handled
        by conditional edges using the routing functions.
    """
    result = state.get("result", {})
    status = result.get("status", "unknown")
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 3)
    
    # Enhanced evaluation logic
    evaluation_result = {
        "status": status,
        "retry_count": retry_count,
        "max_retries": max_retries,
        "evaluation_timestamp": "now",  # Could use actual timestamp
        "decision_reason": ""
    }
    
    if status == "success":
        # Check if the entire goal is complete
        goal_complete = result.get("goal_complete", False)
        evaluation_result.update({
            "decision_reason": "Step completed successfully",
            "goal_complete": goal_complete,
            "next_action": "continue" if not goal_complete else "complete"
        })
    elif status == "error":
        if retry_count < max_retries:
            evaluation_result.update({
                "decision_reason": f"Error occurred, retrying (attempt {retry_count + 1}/{max_retries})",
                "next_action": "retry",
                "retry_count": retry_count + 1
            })
        else:
            evaluation_result.update({
                "decision_reason": "Max retries exceeded, escalating",
                "next_action": "escalate",
                "retry_count": retry_count
            })
    else:
        evaluation_result.update({
            "decision_reason": "Unknown status, escalating",
            "next_action": "escalate"
        })
    
    return {
        "current_step": "evaluate_complete",
        "result": evaluation_result,
        "progress": [f"Evaluated step result: {evaluation_result['decision_reason']}"]
    }
