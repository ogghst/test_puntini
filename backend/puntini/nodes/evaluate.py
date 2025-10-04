"""Evaluate node implementation.

This module implements the evaluate node that decides advance,
retry, or diagnose based on step results using LLM-based evaluation
with structured output for intelligent routing decisions.
"""

from typing import Any, Dict, Optional, Literal, TYPE_CHECKING
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime, get_runtime
from pydantic import BaseModel, Field
from datetime import datetime

if TYPE_CHECKING:
    from ..orchestration.state_schema import State
from ..logging import get_logger
from ..models.errors import ValidationError, AgentError
from ..models.goal_schemas import TodoStatus
from .message import EvaluateResponse, EvaluateResult, Failure, Artifact, ErrorContext, ExecuteToolResponse


def evaluate(
    state: "State", 
    config: Optional[RunnableConfig] = None, 
    runtime: Optional[Runtime] = None
) -> EvaluateResponse:
    """Evaluate the step result and decide next action.
    
    This node evaluates the result from the previous step (typically call_tool)
    and determines the next action based on the evaluation criteria. It uses
    LLM-based evaluation with structured output to make intelligent routing
    decisions between advancing, retrying, or diagnosing issues.
    
    Args:
        state: Current agent state with step execution results.
        config: Optional RunnableConfig for additional configuration.
        runtime: Optional Runtime context for additional runtime information.
        
    Returns:
        Updated state with evaluation results.
        
    Notes:
        Evaluation considers:
        - Tool execution success/failure status
        - Error types and retry patterns
        - Progress towards goal completion
        - Retry limits and escalation thresholds
        - Context from previous steps and failures
        
        The evaluation uses structured LLM output to ensure consistent
        decision-making and proper routing to the next appropriate node.
        
    Raises:
        ValidationError: If state is invalid or missing required data.
        SystemError: If LLM evaluation fails and fallback logic is insufficient.
    """
    # Initialize logger
    logger = get_logger(__name__)
    
    logger.info(f"Evaluating state: {state}")
    
    # Get current step result from execute_tool_response (merged node from Phase 4)
    if isinstance(state, dict):
        execute_tool_response = state.get("execute_tool_response")
    else:
        execute_tool_response = getattr(state, "execute_tool_response", None)
    if not execute_tool_response:
        # Also check for legacy call_tool_response for backward compatibility
        if isinstance(state, dict):
            execute_tool_response = state.get("call_tool_response")
        else:
            execute_tool_response = getattr(state, "call_tool_response", None)
        
        if not execute_tool_response:
            error_msg = "No execute_tool_response found in state for evaluation (neither execute_tool_response nor legacy call_tool_response)"
            logger.error(error_msg)
            return EvaluateResponse(
                current_step="diagnose",
                result=EvaluateResult(
                    status="error",
                    error=error_msg,
                    error_type="validation_error",
                    retry_count=state.get("retry_count", 0) if isinstance(state, dict) else getattr(state, "retry_count", 0),
                    max_retries=state.get("max_retries", 3) if isinstance(state, dict) else getattr(state, "max_retries", 3),
                    evaluation_timestamp=datetime.utcnow().isoformat(),
                    decision_reason="Missing execute_tool_response for evaluation"
                ),
                error_context=ErrorContext(
                    type="validation_error",
                    message=error_msg,
                    details={"missing_component": "execute_tool_response"}
                )
            )
    
    # Extract result information - using ExecuteToolResponse structure
    result = execute_tool_response.result
    tool_name = result.tool_name if hasattr(result, 'tool_name') else None
    execution_status = result.status if hasattr(result, 'status') else getattr(result, 'status', 'unknown')
    execution_time = result.execution_time if hasattr(result, 'execution_time') else getattr(result, 'execution_time', 0.0)
    error = result.error if hasattr(result, 'error') else getattr(result, 'error', None)
    error_type = result.error_type if hasattr(result, 'error_type') else getattr(result, 'error_type', None)
    
    # If tool_name is still None, try to get it from the tool_signature in state
    if not tool_name and isinstance(state, dict):
        tool_signature = state.get("tool_signature")
        if tool_signature and isinstance(tool_signature, dict):
            tool_name = tool_signature.get("tool_name")
    elif not tool_name and hasattr(state, 'tool_signature'):
        tool_signature = getattr(state, 'tool_signature', None)
        if tool_signature and hasattr(tool_signature, 'tool_name'):
            tool_name = tool_signature.tool_name
    
    # Get current retry information
    if isinstance(state, dict):
        retry_count = state.get("retry_count", 0)
        max_retries = state.get("max_retries", 3)
    else:
        retry_count = getattr(state, "retry_count", 0)
        max_retries = getattr(state, "max_retries", 3)
    
    logger.info(f"Evaluating step result: {execution_status} for tool '{tool_name}' (retry {retry_count}/{max_retries})")
    
    try:
        # Get LLM from runtime context for structured evaluation
        if runtime is None:
            try:
                runtime = get_runtime()
            except Exception as e:
                logger.error(f"Failed to get runtime context: {e}")
                return _fallback_evaluation(state, result, retry_count, max_retries, f"Runtime error: {e}")
        
        if not hasattr(runtime, 'context') or 'llm' not in runtime.context:
            logger.warning("LLM not available in runtime context, using fallback evaluation")
            return _fallback_evaluation(state, result, retry_count, max_retries)
        
        llm: BaseChatModel = runtime.context['llm']
        
        # Define structured output schema for evaluation
        class EvaluationDecision(BaseModel):
            """Schema for LLM evaluation decision."""
            decision: Literal["advance", "retry", "diagnose", "escalate"] = Field(
                description="Next action to take"
            )
            confidence: float = Field(ge=0.0, le=1.0, description="Confidence in decision")
            reasoning: str = Field(description="Detailed reasoning for the decision")
            goal_progress: float = Field(ge=0.0, le=1.0, description="Estimated progress towards goal")
            should_retry: bool = Field(description="Whether this step should be retried")
            retry_reason: Optional[str] = Field(default=None, description="Reason for retry if applicable")
            next_action_hint: str = Field(description="Hint for next action")
        
        # Create structured LLM
        structured_llm = llm.with_structured_output(EvaluationDecision)
        
        # Create evaluation prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert evaluator for AI agent step execution. Your task is to evaluate the result of a tool execution and determine the next action.

Available actions:
- "advance": Step was successful, continue to next step or complete
- "retry": Step failed but can be retried with modifications
- "diagnose": Step failed and needs analysis to understand the issue
- "escalate": Step failed repeatedly and needs human intervention

Evaluation criteria:
1. Tool execution status (success/error)
2. Error type and recoverability
3. Current retry count vs max retries
4. Progress towards goal completion
5. Error patterns and context
6. Available fallback options

Guidelines:
- If tool succeeded: advance (unless goal requires more steps)
- If tool failed with recoverable error and retries available: retry
- If tool failed with systematic error or max retries reached: diagnose
- If repeated failures or critical errors: escalate
- Consider the overall goal progress and remaining work
- Be conservative with retries to avoid infinite loops

Return a structured evaluation with clear reasoning."""),
            ("human", """Tool Execution Result:
Tool: {tool_name}
Status: {execution_status}
Execution Time: {execution_time:.3f}s
Error: {error}
Error Type: {error_type}

Current State:
Retry Count: {retry_count}/{max_retries}
Goal: {goal}
Progress: {progress}
Recent Failures: {recent_failures}

Evaluate this result and determine the next action.""")
        ])
        
        # Prepare evaluation context
        if isinstance(state, dict):
            goal = state.get("goal", "Unknown goal")
            progress = state.get("progress", [])
        else:
            goal = getattr(state, "goal", "Unknown goal")
            progress = getattr(state, "progress", [])
        recent_failures = _get_recent_failures(state)
        
        # Create evaluation chain
        evaluation_chain = prompt | structured_llm
        
        # Generate evaluation decision
        evaluation_decision: EvaluationDecision = evaluation_chain.invoke({
            "tool_name": tool_name,
            "execution_status": execution_status,
            "execution_time": execution_time,
            "error": error or "None",
            "error_type": error_type or "None",
            "retry_count": retry_count,
            "max_retries": max_retries,
            "goal": goal,
            "progress": "\n".join(progress[-3:]) if progress else "No progress yet",
            "recent_failures": recent_failures
        })
        
        # Update todo list if step was successful
        updated_todos = []
        todo_updated_description = None
        if evaluation_decision.decision == "advance" and execution_status == "success":
            # Mark corresponding todo as done in state
            todo_updated_description = _mark_todo_done_in_state(state, tool_name, result)
            if todo_updated_description:
                # Get updated todo list from state
                if isinstance(state, dict):
                    updated_todos = state.get("todo_list", [])
                else:
                    updated_todos = getattr(state, "todo_list", [])
        
        # Create evaluation result
        evaluation_result = EvaluateResult(
            status="success",
            retry_count=retry_count,
            max_retries=max_retries,
            evaluation_timestamp=datetime.utcnow().isoformat(),
            decision_reason=evaluation_decision.reasoning,
            goal_complete=evaluation_decision.decision == "advance" and evaluation_decision.goal_progress >= 0.9,
            next_action=evaluation_decision.next_action_hint
        )
        
        # Determine next step based on decision
        if evaluation_decision.decision == "advance":
            next_step = "answer" if evaluation_decision.goal_progress >= 0.9 else "plan_step"
        elif evaluation_decision.decision == "retry":
            next_step = "plan_step"
            # Increment retry count
            retry_count += 1
        elif evaluation_decision.decision == "diagnose":
            next_step = "diagnose"
        else:  # escalate
            next_step = "escalate"
        
        # Create evaluation response with updated artifacts
        artifacts = [Artifact(
            type="evaluation_decision",
            data={
                "decision": evaluation_decision.decision,
                "confidence": evaluation_decision.confidence,
                "reasoning": evaluation_decision.reasoning,
                "goal_progress": evaluation_decision.goal_progress,
                "should_retry": evaluation_decision.should_retry,
                "retry_reason": evaluation_decision.retry_reason,
                "next_action_hint": evaluation_decision.next_action_hint
            }
        )]
        
        # Add todo update artifact if any
        if todo_updated_description:
            artifacts.append(Artifact(
                type="todo_update",
                data={
                    "action": "marked_done",
                    "tool_name": tool_name,
                    "todo_description": todo_updated_description
                }
            ))
        
        # Ensure we always pass the current todo list (updated or not)
        if not updated_todos:
            # Get current todo list from state if no updates were made
            if isinstance(state, dict):
                updated_todos = state.get("todo_list", [])
            else:
                updated_todos = getattr(state, "todo_list", [])
        
        evaluation_response = EvaluateResponse(
            current_step=next_step,
            result=evaluation_result,
            progress=[f"Evaluated step: {evaluation_decision.decision} (confidence: {evaluation_decision.confidence:.2f})"],
            artifacts=artifacts,
            todo_list=updated_todos  # Include updated todo list in response
        )
        
        # Add failure record if this was a retry
        if evaluation_decision.decision == "retry" and error:
            failure = Failure(
                step="call_tool",
                error=error,
                attempt=retry_count,
                error_type=error_type or "unknown"
            )
            if isinstance(state, dict):
                evaluation_response.failures = state.get("failures", []) + [failure]
            else:
                evaluation_response.failures = getattr(state, "failures", []) + [failure]
        
        logger.info(f"Evaluation complete: {evaluation_decision.decision} -> {next_step}")
        
        return evaluation_response
        
    except Exception as e:
        error_msg = f"LLM evaluation failed: {str(e)}"
        logger.error(error_msg)
        
        # Fallback to rule-based evaluation
        return _fallback_evaluation(state, result, retry_count, max_retries, error_msg)


def _fallback_evaluation(
    state: "State", 
    result: Dict[str, Any], 
    retry_count: int, 
    max_retries: int,
    llm_error: Optional[str] = None
) -> EvaluateResponse:
    """Fallback evaluation using rule-based logic when LLM is unavailable.
    
    Args:
        state: Current agent state.
        result: Tool execution result.
        retry_count: Current retry count.
        max_retries: Maximum retry count.
        llm_error: Optional LLM error message.
        
    Returns:
        EvaluateResponse with fallback evaluation decision.
    """
    logger = get_logger(__name__)
    
    # Handle both dict and CallToolResult objects
    if isinstance(result, dict):
        execution_status = result.get("status", "unknown")
        error = result.get("error")
        error_type = result.get("error_type")
        tool_name = result.get("tool_name", "unknown")
    else:
        # CallToolResult Pydantic object
        execution_status = getattr(result, "status", "unknown")
        error = getattr(result, "error", None)
        error_type = getattr(result, "error_type", None)
        tool_name = getattr(result, "tool_name", "unknown")
    
    # Rule-based evaluation logic
    if execution_status == "success":
        decision = "advance"
        reasoning = "Tool execution succeeded"
        goal_progress = 0.8  # Assume good progress for successful execution
    elif retry_count >= max_retries:
        decision = "escalate"
        reasoning = f"Maximum retries ({max_retries}) exceeded"
        goal_progress = 0.0
    elif error_type in ["validation_error", "not_found_error"]:
        decision = "diagnose"
        reasoning = f"Systematic error detected: {error_type}"
        goal_progress = 0.0
    elif error_type in ["tool_error", "network_error"]:
        decision = "retry"
        reasoning = f"Retryable error: {error_type}"
        goal_progress = 0.2
    else:
        decision = "diagnose"
        reasoning = f"Unknown error type: {error_type or 'unknown'}"
        goal_progress = 0.0
    
    # Determine next step
    if decision == "advance":
        next_step = "answer"
    elif decision == "retry":
        next_step = "plan_step"
        retry_count += 1
    elif decision == "diagnose":
        next_step = "diagnose"
    else:  # escalate
        next_step = "escalate"
    
    # Create evaluation result
        evaluation_result = EvaluateResult(
        status="success" if not llm_error else "error",
        error=llm_error,
        error_type="llm_error" if llm_error else None,
            retry_count=retry_count,
            max_retries=max_retries,
        evaluation_timestamp=datetime.utcnow().isoformat(),
        decision_reason=f"Fallback evaluation: {reasoning}",
        goal_complete=decision == "advance" and goal_progress >= 0.9,
        next_action=decision
    )
    
    # Create evaluation response
    evaluation_response = EvaluateResponse(
        current_step=next_step,
        result=evaluation_result,
        progress=[f"Fallback evaluation: {decision} - {reasoning}"],
        artifacts=[Artifact(
            type="fallback_evaluation",
            data={
                "decision": decision,
                "reasoning": reasoning,
                "goal_progress": goal_progress,
                "llm_error": llm_error,
                "retry_count": retry_count
            }
        )]
    )
    
    # Add failure record if this was a retry
    if decision == "retry" and error:
        failure = Failure(
            step="call_tool",
            error=error,
            attempt=retry_count,
            error_type=error_type or "unknown"
        )
        if isinstance(state, dict):
            evaluation_response.failures = state.get("failures", []) + [failure]
        else:
            evaluation_response.failures = getattr(state, "failures", []) + [failure]
    
    logger.info(f"Fallback evaluation: {decision} -> {next_step}")
    
    return evaluation_response


def _mark_todo_done_in_state(state: "State", tool_name: str, result: Dict[str, Any]) -> Optional[str]:
    """Mark a todo item as done in the state's todo list.
    
    Args:
        state: Current agent state.
        tool_name: Name of the tool that was executed.
        result: Result from the tool execution.
        
    Returns:
        Description of the todo that was marked as done, or None if no todo was found.
    """
    logger = get_logger(__name__)
    
    # Get todo list from state
    if isinstance(state, dict):
        todo_list = state.get("todo_list", [])
    else:
        todo_list = getattr(state, "todo_list", [])
    if not todo_list:
        logger.debug("No todo list found in state for update")
        return None
    
    # Try to match the tool execution to a todo item
    for todo in todo_list:
        # Handle both dict and TodoItem objects
        if isinstance(todo, dict):
            todo_status = todo.get("status")
            todo_tool = todo.get("tool_name")
            todo_description = todo.get("description", "")
        else:
            # TodoItem Pydantic object
            todo_status = todo.status
            todo_tool = todo.tool_name
            todo_description = todo.description or ""
        
        if todo_status == "planned":  # Only update planned todos
            # Match by tool name AND description analysis
            if todo_tool == tool_name and _is_todo_completed_by_tool(todo_description, tool_name, result):
                
                # Mark as done
                if isinstance(todo, dict):
                    todo["status"] = "done"
                else:
                    # TodoItem Pydantic object - need to update in place
                    todo.status = TodoStatus.DONE
                logger.info(f"Marked todo as done in state: {todo_description}")
                return todo_description
    
    logger.debug(f"No matching todo found for tool: {tool_name}")
    return None


def _mark_todo_done(state_dict: Dict[str, Any], tool_name: str, result: Dict[str, Any]) -> Optional[str]:
    """Mark a todo item as done based on successful tool execution.
    
    Args:
        state_dict: Current state dictionary.
        tool_name: Name of the tool that was executed.
        result: Result from the tool execution.
        
    Returns:
        Description of the todo that was marked as done, or None if no todo was found.
    """
    logger = get_logger(__name__)
    
    # Get parsed goal data from artifacts
    artifacts = state_dict.get("artifacts", [])
    parsed_goal_data = None
    for artifact in artifacts:
        if artifact.get("type") == "parsed_goal":
            parsed_goal_data = artifact.get("data")
            break
    
    if not parsed_goal_data:
        logger.debug("No parsed goal data found for todo update")
        return None
    
    todo_list = parsed_goal_data.get("todo_list", [])
    if not todo_list:
        logger.debug("No todo list found for update")
        return None
    
    # Try to match the tool execution to a todo item
    for todo in todo_list:
        # Handle both dict and TodoItem objects
        if isinstance(todo, dict):
            todo_status = todo.get("status")
            todo_tool = todo.get("tool_name")
            todo_description = todo.get("description", "")
        else:
            # TodoItem Pydantic object
            todo_status = todo.status
            todo_tool = todo.tool_name
            todo_description = todo.description or ""
        
        if todo_status == "planned":  # Only update planned todos
            # Match by tool name AND description analysis
            if todo_tool == tool_name and _is_todo_completed_by_tool(todo_description, tool_name, result):
                
                # Mark as done
                if isinstance(todo, dict):
                    todo["status"] = "done"
                else:
                    # TodoItem Pydantic object - need to update in place
                    todo.status = TodoStatus.DONE
                logger.info(f"Marked todo as done: {todo_description}")
                return todo_description
    
    logger.debug(f"No matching todo found for tool: {tool_name}")
    return None


def _is_todo_completed_by_tool(todo_description: str, tool_name: str, result: Dict[str, Any]) -> bool:
    """Check if a todo item was completed by the given tool execution.
    
    Args:
        todo_description: Description of the todo item.
        tool_name: Name of the tool that was executed.
        result: Result from the tool execution.
        
    Returns:
        True if the todo was likely completed by this tool execution.
    """
    # Simple heuristic matching based on tool name and todo description
    todo_lower = todo_description.lower()
    
    if tool_name == "add_node":
        return any(keyword in todo_lower for keyword in ["create", "add", "node", "entity"])
    elif tool_name == "add_edge":
        return any(keyword in todo_lower for keyword in ["connect", "link", "relationship", "edge", "between"])
    elif tool_name == "update_props":
        return any(keyword in todo_lower for keyword in ["update", "modify", "change", "property", "attribute"])
    elif tool_name == "delete_node":
        return any(keyword in todo_lower for keyword in ["delete", "remove", "node", "entity"])
    elif tool_name == "delete_edge":
        return any(keyword in todo_lower for keyword in ["delete", "remove", "relationship", "edge"])
    elif tool_name in ["query_graph", "cypher_query"]:
        return any(keyword in todo_lower for keyword in ["query", "search", "find", "get", "retrieve"])
    
    return False


def _get_recent_failures(state: "State") -> str:
    """Get recent failures for evaluation context.
    
    Args:
        state: Current agent state.
        
    Returns:
        Formatted string of recent failures.
    """
    if isinstance(state, dict):
        failures = state.get("failures", [])
    else:
        failures = getattr(state, "failures", [])
    if not failures:
        return "No recent failures"
    
    # Get last 3 failures
    recent_failures = failures[-3:] if len(failures) > 3 else failures
    failure_lines = []
    
    for failure in recent_failures:
        if isinstance(failure, dict):
            step = failure.get("step", "unknown")
            error = failure.get("error", "unknown error")
            error_type = failure.get("error_type", "unknown")
            attempt = failure.get("attempt", 0)
            failure_lines.append(f"- {step} (attempt {attempt}): {error_type} - {error}")
        else:
            # Handle Pydantic model
            failure_lines.append(f"- {failure.step} (attempt {failure.attempt}): {failure.error_type} - {failure.error}")
    
    return "\n".join(failure_lines) if failure_lines else "No recent failures"
