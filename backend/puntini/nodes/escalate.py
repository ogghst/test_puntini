"""Escalate node implementation.

This module implements the escalate node that handles escalation
to human input with checkpointing and deterministic resume.
"""

from typing import Any, Dict, Optional, TYPE_CHECKING
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime

if TYPE_CHECKING:
    from ..orchestration.state_schema import State
from .message import EscalateResponse, EscalateContext


def escalate(
    state: "State",
    config: Optional[RunnableConfig] = None,
    runtime: Optional[Runtime] = None
) -> EscalateResponse:
    """Handle escalation to human input.
    
    This node prepares the escalation context and interrupts
    execution for human input when needed.
    
    Args:
        state: Current agent state with escalation context.
        config: Optional RunnableConfig for additional configuration.
        runtime: Optional Runtime context for additional runtime information.
        
    Returns:
        EscalateResponse with escalation context and routing information.
        
    Notes:
        Escalation should provide clear context and options
        for human decision-making and enable deterministic resume.
    """
    # Convert state to dict if needed
    if isinstance(state, dict):
        state_dict = state
    else:
        # Convert Pydantic model to dictionary
        state_dict = state.model_dump() if hasattr(state, 'model_dump') else state.__dict__
    
    # Get error context for escalation
    error_context = state_dict.get("error_context")
    error_message = "Unknown error occurred"
    
    if error_context:
        if isinstance(error_context, dict):
            error_message = error_context.get("message", "Unknown error")
        else:
            error_message = error_context.message if hasattr(error_context, 'message') else "Unknown error"
    
    # Create escalation context with clear options
    escalation_context = EscalateContext(
        reason="Agent requires human intervention",
        error=error_message,
        options=[
            "Retry with different approach",
            "Skip this step and continue",
            "Abort execution",
            "Provide additional context"
        ],
        recommended_action="Retry with different approach"
    )
    
    # Create escalation response
    response = EscalateResponse(
        current_step="answer",
        escalation_context=escalation_context
    )
    
    return response
