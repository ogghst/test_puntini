"""Answer node implementation.

This module implements the answer node that synthesizes the
final answer and closes the execution cleanly.
"""

from typing import Any, Dict, Optional, TYPE_CHECKING
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime

if TYPE_CHECKING:
    from ..orchestration.state_schema import State
from .message import AnswerResponse, AnswerResult


def answer(
    state: "State",
    config: Optional[RunnableConfig] = None,
    runtime: Optional[Runtime] = None
) -> AnswerResponse:
    """Synthesize final answer and close cleanly.
    
    This node creates the final answer based on the execution
    results and prepares the state for clean completion.
    
    Args:
        state: Current agent state with execution results.
        config: Optional RunnableConfig for additional configuration.
        runtime: Optional Runtime context for additional runtime information.
        
    Returns:
        AnswerResponse with final answer and completion information.
        
    Notes:
        The answer should summarize the execution results and
        provide a clear conclusion to the agent's task.
    """
    # Convert state to dict if needed
    if isinstance(state, dict):
        state_dict = state
    else:
        # Convert Pydantic model to dictionary
        state_dict = state.model_dump() if hasattr(state, 'model_dump') else state.__dict__
    
    # Get execution information
    result = state_dict.get("result", {})
    progress = state_dict.get("progress", [])
    artifacts = state_dict.get("artifacts", [])
    failures = state_dict.get("failures", [])
    
    # Determine completion status
    if failures:
        status = "completed_with_errors"
        summary = f"Task completed with {len(failures)} error(s) encountered"
    else:
        status = "success"
        summary = "Task execution completed successfully"
    
    # Create final answer
    final_answer = AnswerResult(
        status=status,
        summary=summary,
        steps_taken=len(progress),
        artifacts_created=len(artifacts),
        final_result=result
    )
    
    # Create answer response
    response = AnswerResponse(
        current_step="complete",
        result=final_answer
    )
    
    return response
