"""Diagnose node implementation.

This module implements the diagnose node that classifies failures
and chooses appropriate remediation strategies.
"""

from typing import Any, Dict, Optional, TYPE_CHECKING
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime

if TYPE_CHECKING:
    from ..orchestration.state_schema import State
from .message import DiagnoseResponse, DiagnoseResult, Artifact, ErrorContext


def diagnose(
    state: "State",
    config: Optional[RunnableConfig] = None,
    runtime: Optional[Runtime] = None
) -> DiagnoseResponse:
    """Diagnose failures and determine remediation.
    
    This node analyzes the failure that occurred and determines
    the appropriate remediation strategy based on the error type.
    
    Args:
        state: Current agent state with error information.
        config: Optional RunnableConfig for additional configuration.
        runtime: Optional Runtime context for additional runtime information.
        
    Returns:
        DiagnoseResponse with diagnosis results and routing information.
        
    Notes:
        Diagnosis should classify errors as identical, random, or
        systematic to determine the appropriate retry strategy.
    """
    # Convert state to dict if needed
    if isinstance(state, dict):
        state_dict = state
    else:
        # Convert Pydantic model to dictionary
        state_dict = state.model_dump() if hasattr(state, 'model_dump') else state.__dict__
    
    # Get error information
    result = state_dict.get("result", {})
    error = result.get("error", "Unknown error") if result else "Unknown error"
    error_type = result.get("error_type", "unknown") if result else "unknown"
    
    # Get error context if available
    error_context = state_dict.get("error_context")
    if error_context and isinstance(error_context, dict):
        error_type = error_context.get("type", error_type)
        error = error_context.get("message", error)
    
    # Classify error and determine remediation strategy
    if error_type == "identical":
        # Same error repeated - escalate
        error_classification = "identical"
        remediation_strategy = "escalate"
        confidence = 0.9
        recommended_action = "escalate"
        next_step = "escalate"
    elif error_type == "random":
        # Random error - retry
        error_classification = "random"
        remediation_strategy = "retry"
        confidence = 0.7
        recommended_action = "plan_step"
        next_step = "plan_step"
    else:
        # Systematic error - escalate for human input
        error_classification = "systematic"
        remediation_strategy = "escalate"
        confidence = 0.8
        recommended_action = "escalate"
        next_step = "escalate"
    
    # Create diagnosis result
    diagnosis_result = DiagnoseResult(
        status="success",
        error_classification=error_classification,
        remediation_strategy=remediation_strategy,
        confidence=confidence,
        recommended_action=recommended_action
    )
    
    # Create error context
    error_context = ErrorContext(
        type=error_classification,
        message=error,
        details={
            "original_error_type": error_type,
            "confidence": confidence,
            "strategy": remediation_strategy
        }
    )
    
    # Create diagnosis response
    response = DiagnoseResponse(
        current_step=next_step,
        result=diagnosis_result
    )
    
    return response
