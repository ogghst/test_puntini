"""LangGraph state machine definition.

This module defines the main LangGraph state machine with nodes, edges,
and conditional routing for the agent's execution flow.
"""

from typing import Any, Dict, Literal, Optional, Union
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.types import Command
from langgraph.runtime import Runtime
from langchain_core.runnables import RunnableConfig

from .state_schema import State
from .checkpointer import create_checkpointer, get_checkpoint_config
from ..nodes.message import (
    ParseGoalResult, EvaluateResult, DiagnoseResult, ErrorContext, EscalateContext,
    AnswerResult, ParseGoalResponse, PlanStepResponse, RouteToolResponse,
    CallToolResponse, EvaluateResponse, DiagnoseResponse, EscalateResponse, AnswerResponse
)
from ..nodes.return_types import (
    ParseGoalReturn, PlanStepReturn, RouteToolReturn, CallToolReturn,
    DiagnoseReturn, AnswerReturn, EvaluateCommandReturn, EscalateCommandReturn
)


def route_after_parse_goal(state: State) -> str:
    """Route after parsing goal based on complexity and parsing results.
    
    Args:
        state: Current agent state with parsed goal information.
        
    Returns:
        The next node to execute.
    """
    # Convert state to dict if needed
    if isinstance(state, dict):
        state_dict = state
    else:
        # Convert Pydantic model to dictionary
        state_dict = state.model_dump() if hasattr(state, 'model_dump') else state.__dict__
    
    # Get the parse goal response from state
    parse_response = state_dict.get("parse_goal_response")
    
    # If no response or parsing failed, route to diagnose
    if not parse_response:
        return "diagnose"
    
    # Check if parsing failed (handle both dict and object responses)
    if isinstance(parse_response, dict):
        result = parse_response.get("result", {})
        if result.get("status") == "error":
            return "diagnose"
        return parse_response.get("current_step", "diagnose")
    else:
        # Handle object response
        if parse_response.result.status == "error":
            return "diagnose"
        return parse_response.current_step


def route_after_evaluate(state: State) -> str:
    """Route after evaluation based on step results.
    
    Args:
        state: Current agent state with evaluation results.
        
    Returns:
        The next node to execute.
    """
    # Convert state to dict if needed
    if isinstance(state, dict):
        state_dict = state
    else:
        # Convert Pydantic model to dictionary
        state_dict = state.model_dump() if hasattr(state, 'model_dump') else state.__dict__
    
    # Get the evaluate response from state
    evaluate_response = state_dict.get("evaluate_response")
    
    # If no response, default to escalate
    if not evaluate_response:
        return "escalate"
    
    # Handle both dict and object responses
    if isinstance(evaluate_response, dict):
        result = evaluate_response.get("result", {})
        status = result.get("status", "error")
        retry_count = result.get("retry_count", 0)
        max_retries = result.get("max_retries", 3)
    else:
        result = evaluate_response.result
        status = result.status
        retry_count = result.retry_count
        max_retries = result.max_retries
    
    if status == "success":
        # Check if goal is complete
        goal_complete = result.get("goal_complete", False) if isinstance(result, dict) else result.goal_complete
        if goal_complete:
            return "answer"
        else:
            return "plan_step"  # Continue with next step
    elif status == "error" and retry_count < max_retries:
        return "diagnose"
    else:
        return "escalate"


def route_after_diagnose(state: State) -> str:
    """Route after diagnosis based on error classification.
    
    Args:
        state: Current agent state with diagnosis results.
        
    Returns:
        The next node to execute.
    """
    # Convert state to dict if needed
    if isinstance(state, dict):
        state_dict = state
    else:
        # Convert Pydantic model to dictionary
        state_dict = state.model_dump() if hasattr(state, 'model_dump') else state.__dict__
    
    # Get the diagnose response from state
    diagnose_response = state_dict.get("diagnose_response")
    error_context = state_dict.get("error_context")
    
    # If no response, default to escalate
    if not diagnose_response:
        return "escalate"
    
    # Handle both dict and object responses
    if isinstance(diagnose_response, dict):
        result = diagnose_response.get("result", {})
    else:
        result = diagnose_response.result
    
    # Handle error context
    if isinstance(error_context, dict):
        error_type = error_context.get("type", "unknown")
    else:
        error_type = error_context.type if error_context else "unknown"
    
    if error_type == "identical":
        # Identical error, escalate
        return "escalate"
    elif error_type == "random":
        # Random error, retry
        return "plan_step"
    elif error_type == "systematic":
        # Systematic error, escalate for human input
        return "escalate"
    else:
        # Unknown error, escalate
        return "escalate"


def parse_goal(state: State, config: Optional[RunnableConfig] = None, runtime: Optional[Runtime] = None) -> Dict[str, Any]:
    """Parse the goal and extract structured information.
    
    This function delegates to the actual parse_goal implementation
    in the nodes module to maintain separation of concerns.
    
    Args:
        state: Current agent state.
        config: Optional RunnableConfig for additional configuration.
        runtime: Optional Runtime context for additional runtime information.
        
    Returns:
        Dictionary with parsed goal information and state updates.
    """
    from ..nodes.parse_goal import parse_goal as parse_goal_impl
    
    # Call the implementation and get the response
    response = parse_goal_impl(state, config, runtime)
    
    # Convert state to dict if needed
    if isinstance(state, dict):
        state_dict = state
    else:
        # Convert Pydantic model to dictionary
        state_dict = state.model_dump() if hasattr(state, 'model_dump') else state.__dict__
    
    # Create the proper return type and convert to state update
    return_obj = ParseGoalReturn(
        current_step=response.current_step,
        current_attempt=response.current_attempt,
        progress=state_dict.get("progress", []) + response.progress,
        artifacts=state_dict.get("artifacts", []) + response.artifacts,
        failures=state_dict.get("failures", []) + response.failures,
        result=response.result.model_dump() if response.result else None,
        parse_goal_response=response
    )
    
    return return_obj.to_state_update()


def plan_step(state: State, config: Optional[RunnableConfig] = None, runtime: Optional[Runtime] = None) -> Dict[str, Any]:
    """Plan the next step in the agent's execution.
    
    Args:
        state: Current agent state.
        config: Optional RunnableConfig for additional configuration.
        runtime: Optional Runtime context for additional runtime information.
        
    Returns:
        Dictionary with planned step information and state updates.
    """
    from ..nodes.plan_step import plan_step as plan_step_impl
    
    # Call the implementation and get the response
    response = plan_step_impl(state, config, runtime)
    
    # Convert state to dict if needed
    if isinstance(state, dict):
        state_dict = state
    else:
        # Convert Pydantic model to dictionary
        state_dict = state.model_dump() if hasattr(state, 'model_dump') else state.__dict__
    
    # Create the proper return type and convert to state update
    return_obj = PlanStepReturn(
        current_step=response.current_step,
        progress=state_dict.get("progress", []) + response.progress,
        artifacts=state_dict.get("artifacts", []) + response.artifacts,
        failures=state_dict.get("failures", []) + response.failures,
        result=response.result.model_dump() if response.result else None,
        plan_step_response=response,
        tool_signature=response.tool_signature
    )
    
    return return_obj.to_state_update()


def route_tool(state: State, config: Optional[RunnableConfig] = None, runtime: Optional[Runtime] = None) -> Dict[str, Any]:
    """Route to the appropriate tool or branch.
    
    This function delegates to the actual route_tool implementation
    in the nodes module to maintain separation of concerns.
    
    Args:
        state: Current agent state.
        config: Optional RunnableConfig for additional configuration.
        runtime: Optional Runtime context for additional runtime information.
        
    Returns:
        Dictionary with routing decision and state updates.
    """
    from ..nodes.route_tool import route_tool as route_tool_impl
    
    # Call the implementation and get the response
    response = route_tool_impl(state, config, runtime)
    
    # Convert state to dict if needed
    if isinstance(state, dict):
        state_dict = state
    else:
        # Convert Pydantic model to dictionary
        state_dict = state.model_dump() if hasattr(state, 'model_dump') else state.__dict__
    
    # Create the proper return type and convert to state update
    return_obj = RouteToolReturn(
        current_step=response.current_step,
        progress=state_dict.get("progress", []) + response.progress,
        artifacts=state_dict.get("artifacts", []) + response.artifacts,
        failures=state_dict.get("failures", []) + response.failures,
        result=response.result.model_dump() if response.result else None,
        route_tool_response=response,
        tool_signature=response.tool_signature
    )
    
    return return_obj.to_state_update()


def call_tool(state: State, config: Optional[RunnableConfig] = None, runtime: Optional[Runtime] = None) -> Dict[str, Any]:
    """Execute the selected tool.
    
    This function delegates to the actual call_tool implementation
    in the nodes module to maintain separation of concerns.
    
    Args:
        state: Current agent state.
        config: Optional RunnableConfig for additional configuration.
        runtime: Optional Runtime context for additional runtime information.
        
    Returns:
        Dictionary with tool execution result and state updates.
    """
    from ..nodes.call_tool import call_tool as call_tool_impl
    
    # Call the implementation and get the response
    response = call_tool_impl(state, config, runtime)
    
    # Convert state to dict if needed
    if isinstance(state, dict):
        state_dict = state
    else:
        # Convert Pydantic model to dictionary
        state_dict = state.model_dump() if hasattr(state, 'model_dump') else state.__dict__
    
    # Create the proper return type and convert to state update
    return_obj = CallToolReturn(
        current_step=response.current_step,
        progress=state_dict.get("progress", []) + response.progress,
        artifacts=state_dict.get("artifacts", []) + response.artifacts,
        failures=state_dict.get("failures", []) + response.failures,
        result=response.result.model_dump() if response.result else None,
        call_tool_response=response
    )
    
    return return_obj.to_state_update()


def evaluate(state: State) -> Command:
    """Evaluate the step result and decide next action.
    
    Args:
        state: Current agent state.
        
    Returns:
        Command with next node and state updates.
    """
    # Convert state to dict if needed
    if isinstance(state, dict):
        state_dict = state
    else:
        # Convert Pydantic model to dictionary
        state_dict = state.model_dump() if hasattr(state, 'model_dump') else state.__dict__
    
    # TODO: Implement evaluation logic
    # For now, use a simple evaluation based on current result
    result = state_dict.get("result")
    if result and result.get("status") == "success":
        return Command(update={"current_step": "answer"}, goto="answer")
    else:
        return Command(update={"current_step": "diagnose"}, goto="diagnose")


def diagnose(state: State) -> Dict[str, Any]:
    """Diagnose failures and determine remediation.
    
    Args:
        state: Current agent state.
        
    Returns:
        Dictionary with diagnosis results and state updates.
    """
    # TODO: Implement diagnosis logic
    # For now, create a simple diagnosis response
    from ..nodes.message import DiagnoseResponse, DiagnoseResult, ErrorContext
    
    # Convert state to dict if needed
    if isinstance(state, dict):
        state_dict = state
    else:
        # Convert Pydantic model to dictionary
        state_dict = state.model_dump() if hasattr(state, 'model_dump') else state.__dict__
    
    # Create error context if not present
    error_context = state_dict.get("error_context") or ErrorContext(
        type="systematic",
        message="Unknown error",
        details={}
    )
    
    # Create diagnosis result
    diagnosis_result = DiagnoseResult(
        status="success",
        error_classification="systematic",
        remediation_strategy="escalate",
        confidence=0.8,
        recommended_action="escalate"
    )
    
    # Create diagnosis response
    diagnosis_response = DiagnoseResponse(
        current_step="escalate",
        result=diagnosis_result
    )
    
    # Create the proper return type and convert to state update
    return_obj = DiagnoseReturn(
        current_step="escalate",
        progress=[],
        artifacts=[],
        failures=[],
        result=diagnosis_result.model_dump(),
        diagnose_response=diagnosis_response,
        error_context=error_context
    )
    
    return return_obj.to_state_update()


def escalate(state: State) -> Command:
    """Handle escalation to human input.
    
    Args:
        state: Current agent state.
        
    Returns:
        Command with escalation handling.
    """
    # TODO: Implement escalation logic
    # For now, create a simple escalation response
    from ..nodes.message import EscalateResponse, EscalateContext
    
    # Convert state to dict if needed
    if isinstance(state, dict):
        state_dict = state
    else:
        # Convert Pydantic model to dictionary
        state_dict = state.model_dump() if hasattr(state, 'model_dump') else state.__dict__
    
    # Create escalation context if not present
    escalation_context = state_dict.get("escalation_context") or EscalateContext(
        reason="Unknown error occurred",
        error="System error",
        options=["Retry", "Skip", "Abort"],
        recommended_action="Retry"
    )
    
    # Create escalation response
    escalation_response = EscalateResponse(
        current_step="answer",
        escalation_context=escalation_context
    )
    
    return Command(
        update={
            "escalate_response": escalation_response,
            "escalation_context": escalation_context,
            "current_step": "answer"
        },
        goto="answer"
    )


def answer(state: State) -> Dict[str, Any]:
    """Synthesize final answer and close cleanly.
    
    Args:
        state: Current agent state.
        
    Returns:
        Dictionary with final answer and state updates.
    """
    # TODO: Implement answer synthesis logic
    from ..nodes.message import AnswerResponse, AnswerResult
    
    # Convert state to dict if needed
    if isinstance(state, dict):
        state_dict = state
    else:
        # Convert Pydantic model to dictionary
        state_dict = state.model_dump() if hasattr(state, 'model_dump') else state.__dict__
    
    # Create answer result
    answer_result = AnswerResult(
        status="success",
        summary="Task completed successfully",
        steps_taken=len(state_dict.get("progress", [])),
        artifacts_created=len(state_dict.get("artifacts", [])),
        final_result={"answer": "Task completed successfully"}
    )
    
    # Create answer response
    answer_response = AnswerResponse(
        current_step="complete",
        result=answer_result
    )
    
    # Create the proper return type and convert to state update
    return_obj = AnswerReturn(
        current_step="complete",
        progress=[],
        artifacts=[],
        failures=[],
        result=answer_result.model_dump(),
        answer_response=answer_response
    )
    
    return return_obj.to_state_update()


def create_agent_graph(checkpointer: BaseCheckpointSaver | None = None) -> StateGraph:
    """Create the agent's LangGraph state machine.
    
    Args:
        checkpointer: Optional checkpointer for state persistence.
        
    Returns:
        Compiled LangGraph state machine.
        
    Notes:
        The graph implements the state machine defined in AGENTS.md with
        nodes for parsing, planning, routing, execution, evaluation,
        diagnosis, escalation, and answering.
    """
    # Create the state graph
    workflow = StateGraph(State)
    
    # Add nodes
    workflow.add_node("parse_goal", parse_goal)
    workflow.add_node("plan_step", plan_step)
    workflow.add_node("route_tool", route_tool)
    workflow.add_node("call_tool", call_tool)
    workflow.add_node("evaluate", evaluate)
    workflow.add_node("diagnose", diagnose)
    workflow.add_node("escalate", escalate)
    workflow.add_node("answer", answer)
    
    # Add edges
    workflow.add_edge(START, "parse_goal")
    
    # Conditional routing after parse_goal
    workflow.add_conditional_edges(
        "parse_goal",
        route_after_parse_goal,
        {
            "plan_step": "plan_step",
            "route_tool": "route_tool", 
            "diagnose": "diagnose"
        }
    )
    
    # Direct edges for planning and routing
    workflow.add_edge("plan_step", "route_tool")
    workflow.add_edge("route_tool", "call_tool")
    
    # Conditional routing after evaluate
    workflow.add_conditional_edges(
        "evaluate",
        route_after_evaluate,
        {
            "plan_step": "plan_step",
            "diagnose": "diagnose",
            "escalate": "escalate",
            "answer": "answer"
        }
    )
    
    # Conditional routing after diagnose
    workflow.add_conditional_edges(
        "diagnose",
        route_after_diagnose,
        {
            "plan_step": "plan_step",
            "escalate": "escalate"
        }
    )
    
    # Direct edges for escalation and completion
    workflow.add_edge("escalate", "answer")
    workflow.add_edge("answer", END)
    
    # Compile the graph
    if checkpointer:
        return workflow.compile(checkpointer=checkpointer)
    else:
        return workflow.compile()


def create_agent_with_checkpointer(checkpointer_type: str = "memory", **kwargs: Any) -> StateGraph:
    """Create an agent with a specific checkpointer type.
    
    Args:
        checkpointer_type: Type of checkpointer to use.
        **kwargs: Additional configuration parameters.
        
    Returns:
        Compiled LangGraph state machine with checkpointer.
    """
    checkpointer = create_checkpointer(checkpointer_type, **kwargs)
    return create_agent_graph(checkpointer)


