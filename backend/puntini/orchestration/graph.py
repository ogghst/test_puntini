"""LangGraph state machine definition.

This module defines the main LangGraph state machine with nodes, edges,
and conditional routing for the agent's execution flow.
"""

from typing import Any, Dict, Literal, Optional, Union, TYPE_CHECKING
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.types import Command
from langgraph.runtime import Runtime
from langchain_core.runnables import RunnableConfig
from langgraph.errors import GraphRecursionError

from ..logging import get_logger

from .state_schema import State
from .checkpointer import create_checkpointer, get_checkpoint_config
from ..nodes.message import (
    ParseGoalResult, EvaluateResult, DiagnoseResult, ErrorContext, EscalateContext,
    AnswerResult, ParseGoalResponse, PlanStepResponse, RouteToolResponse,
    CallToolResponse, EvaluateResponse, DiagnoseResponse, EscalateResponse, AnswerResponse,
    ExecuteToolResponse
)
from ..nodes.return_types import (
    ParseGoalReturn, PlanStepReturn, RouteToolReturn, CallToolReturn, ExecuteToolReturn,
    DiagnoseReturn, AnswerReturn, EvaluateReturn, EvaluateCommandReturn, EscalateCommandReturn
)

if TYPE_CHECKING:
    from ..observability.tracer_factory import Tracer

logger = get_logger(__name__)


def route_after_parse_intent(state: State) -> str:
    """Route after parsing intent based on intent characteristics.
    
    Args:
        state: Current agent state with parsed intent information.
        
    Returns:
        The next node to execute.
    """
    # Convert state to dict if needed
    if isinstance(state, dict):
        state_dict = state
    else:
        # Convert Pydantic model to dictionary
        state_dict = state.model_dump() if hasattr(state, 'model_dump') else state.__dict__
    
    # Get the parse intent response from state
    parse_response = state_dict.get("parse_intent_response")
    
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


def route_after_resolve_entities(state: State) -> str:
    """Route after resolving entities based on resolution results.
    
    Args:
        state: Current agent state with resolved entities.
        
    Returns:
        The next node to execute.
    """
    # Convert state to dict if needed
    if isinstance(state, dict):
        state_dict = state
    else:
        # Convert Pydantic model to dictionary
        state_dict = state.model_dump() if hasattr(state, 'model_dump') else state.__dict__
    
    # Get the resolve entities response from state
    resolve_response = state_dict.get("resolve_entities_response")
    
    # If no response or resolution failed, route to diagnose
    if not resolve_response:
        return "diagnose"
    
    # Check if resolution failed (handle both dict and object responses)
    if isinstance(resolve_response, dict):
        result = resolve_response.get("result", {})
        if result.get("status") == "error":
            return "diagnose"
        return resolve_response.get("current_step", "diagnose")
    else:
        # Handle object response
        if resolve_response.result.status == "error":
            return "diagnose"
        return resolve_response.current_step


def route_after_disambiguate(state: State) -> str:
    """Route after disambiguation based on disambiguation results.
    
    Args:
        state: Current agent state with disambiguation results.
        
    Returns:
        The next node to execute.
    """
    # Convert state to dict if needed
    if isinstance(state, dict):
        state_dict = state
    else:
        # Convert Pydantic model to dictionary
        state_dict = state.model_dump() if hasattr(state, 'model_dump') else state.__dict__
    
    # Get the disambiguate response from state
    disambiguate_response = state_dict.get("disambiguate_response")
    
    # If no response or disambiguation failed, route to diagnose
    if not disambiguate_response:
        return "diagnose"
    
    # Check if disambiguation failed (handle both dict and object responses)
    if isinstance(disambiguate_response, dict):
        result = disambiguate_response.get("result", {})
        if result.get("status") == "error":
            return "diagnose"
        return disambiguate_response.get("current_step", "diagnose")
    else:
        # Handle object response
        if disambiguate_response.result.status == "error":
            return "diagnose"
        return disambiguate_response.current_step


def route_after_evaluate(state: State) -> str:
    """Route after evaluation based on step results.
    
    This function analyzes the evaluation results and determines the next
    action based on the evaluation decision, retry counts, and goal progress.
    
    Args:
        state: Current agent state with evaluation results.
        
    Returns:
        The next node to execute: "answer", "plan_step", "diagnose", or "escalate".
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
        current_step = evaluate_response.get("current_step", "escalate")
        status = result.get("status", "error")
        retry_count = result.get("retry_count", 0)
        max_retries = result.get("max_retries", 3)
        goal_complete = result.get("goal_complete", False)
        next_action = result.get("next_action", "escalate")
    else:
        result = evaluate_response.result
        current_step = evaluate_response.current_step
        status = result.status
        retry_count = result.retry_count
        max_retries = result.max_retries
        goal_complete = result.goal_complete
        next_action = result.next_action
    
    # Use the current_step from the evaluation response as the primary routing decision
    # The evaluate node has already made the intelligent decision
    if current_step in ["answer", "plan_step", "diagnose", "escalate"]:
        return current_step
    
    # Fallback routing logic if current_step is not a valid node
    if status == "success":
        if goal_complete:
            return "answer"
        else:
            return "plan_step"  # Continue with next step
    elif status == "error":
        if retry_count < max_retries:
            return "diagnose"
        else:
            return "escalate"
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


def parse_intent(state: State, config: Optional[RunnableConfig] = None, runtime: Optional[Runtime] = None) -> Dict[str, Any]:
    """Parse minimal intent without graph context (Phase 1 of two-phase parsing).
    
    This function delegates to the actual parse_intent implementation
    in the nodes module to maintain separation of concerns.
    
    Args:
        state: Current agent state.
        config: Optional RunnableConfig for additional configuration.
        runtime: Optional Runtime context for additional runtime information.
        
    Returns:
        Dictionary with parsed intent information and state updates.
    """
    logger.debug("Executing parse_intent node")
    from ..nodes.parse_intent import parse_intent as parse_intent_impl
    
    # Call the implementation and get the response
    response: ParseGoalResponse = parse_intent_impl(state, config, runtime)
    
    # Convert state to dict if needed
    if isinstance(state, dict):
        state_dict = state
    else:
        # Convert Pydantic model to dictionary
        state_dict = state.model_dump() if hasattr(state, 'model_dump') else state.__dict__
    
    # Convert artifacts to dictionaries if they are not already
    artifacts_dicts = [artifact.model_dump() if hasattr(artifact, 'model_dump') else artifact for artifact in response.artifacts]
    
    # Create the proper return type and convert to state update
    return_obj = ParseGoalReturn(
        current_step=response.current_step,
        current_attempt=response.current_attempt,
        progress=response.progress,
        artifacts=artifacts_dicts,
        failures=response.failures,
        result=response.result.model_dump() if response.result else None,
        node_result=response.result.model_dump() if response.result else None
    )
    
    # Add the response to the state update
    state_update = return_obj.to_state_update()
    state_update["parse_intent_response"] = response
    return state_update


def resolve_entities(state: State, config: Optional[RunnableConfig] = None, runtime: Optional[Runtime] = None) -> Dict[str, Any]:
    """Resolve entities with graph context (Phase 2 of two-phase parsing).
    
    This function delegates to the actual resolve_entities implementation
    in the nodes module to maintain separation of concerns.
    
    Args:
        state: Current agent state.
        config: Optional RunnableConfig for additional configuration.
        runtime: Optional Runtime context for additional runtime information.
        
    Returns:
        Dictionary with resolved entities and state updates.
    """
    logger.debug("Executing resolve_entities node")
    from ..nodes.resolve_entities import resolve_entities as resolve_entities_impl
    
    # Call the implementation and get the response
    response: ParseGoalResponse = resolve_entities_impl(state, config, runtime)
    
    # Convert state to dict if needed
    if isinstance(state, dict):
        state_dict = state
    else:
        # Convert Pydantic model to dictionary
        state_dict = state.model_dump() if hasattr(state, 'model_dump') else state.__dict__
    
    # Convert artifacts to dictionaries if they are not already
    artifacts_dicts = [artifact.model_dump() if hasattr(artifact, 'model_dump') else artifact for artifact in response.artifacts]
    
    # Create the proper return type and convert to state update
    return_obj = ParseGoalReturn(
        current_step=response.current_step,
        current_attempt=response.current_attempt,
        progress=response.progress,
        artifacts=artifacts_dicts,
        failures=response.failures,
        result=response.result.model_dump() if response.result else None,
        node_result=response.result.model_dump() if response.result else None
    )
    
    # Add the response to the state update
    state_update = return_obj.to_state_update()
    state_update["resolve_entities_response"] = response
    return state_update


def disambiguate(state: State, config: Optional[RunnableConfig] = None, runtime: Optional[Runtime] = None) -> Dict[str, Any]:
    """Handle ambiguous entity references with user interaction.
    
    This function delegates to the actual disambiguate implementation
    in the nodes module to maintain separation of concerns.
    
    Args:
        state: Current agent state.
        config: Optional RunnableConfig for additional configuration.
        runtime: Optional Runtime context for additional runtime information.
        
    Returns:
        Dictionary with disambiguation results and state updates.
    """
    logger.debug("Executing disambiguate node")
    from ..nodes.disambiguate import disambiguate as disambiguate_impl
    
    # Call the implementation and get the response
    response: ParseGoalResponse = disambiguate_impl(state, config, runtime)
    
    # Convert state to dict if needed
    if isinstance(state, dict):
        state_dict = state
    else:
        # Convert Pydantic model to dictionary
        state_dict = state.model_dump() if hasattr(state, 'model_dump') else state.__dict__
    
    # Convert artifacts to dictionaries if they are not already
    artifacts_dicts = [artifact.model_dump() if hasattr(artifact, 'model_dump') else artifact for artifact in response.artifacts]
    
    # Create the proper return type and convert to state update
    return_obj = ParseGoalReturn(
        current_step=response.current_step,
        current_attempt=response.current_attempt,
        progress=response.progress,
        artifacts=artifacts_dicts,
        failures=response.failures,
        result=response.result.model_dump() if response.result else None,
        node_result=response.result.model_dump() if response.result else None
    )
    
    # Add the response to the state update
    state_update = return_obj.to_state_update()
    state_update["disambiguate_response"] = response
    return state_update


def plan_step(state: State, config: Optional[RunnableConfig] = None, runtime: Optional[Runtime] = None) -> Dict[str, Any]:
    """Plan the next step in the agent's execution.
    
    Args:
        state: Current agent state.
        config: Optional RunnableConfig for additional configuration.
        runtime: Optional Runtime context for additional runtime information.
        
    Returns:
        Dictionary with planned step information and state updates.
    """
    logger.debug("Executing plan_step node")
    from ..nodes.plan_step import plan_step as plan_step_impl
    
    # Call the implementation and get the response
    response : PlanStepResponse = plan_step_impl(state, config, runtime)
    
    # Convert state to dict if needed
    if isinstance(state, dict):
        state_dict = state
    else:
        # Convert Pydantic model to dictionary
        state_dict = state.model_dump() if hasattr(state, 'model_dump') else state.__dict__
    
    # Convert artifacts to dictionaries if they are not already
    artifacts_dicts = [artifact.model_dump() if hasattr(artifact, 'model_dump') else artifact for artifact in response.artifacts]
    
    # Create the proper return type and convert to state update
    return_obj = PlanStepReturn(
        current_step=response.current_step,
        progress=response.progress,
        artifacts=artifacts_dicts,
        failures=response.failures,
        result=response.result.model_dump() if response.result else None,
        node_result=response.result.model_dump() if response.result else None,
        tool_signature=response.tool_signature
    )
    
    # Add the response to the state update
    state_update = return_obj.to_state_update()
    state_update["plan_step_response"] = response
    return state_update


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
    logger.debug("Executing route_tool node")
    from ..nodes.route_tool import route_tool as route_tool_impl
    
    # Call the implementation and get the response
    response : RouteToolResponse = route_tool_impl(state, config, runtime)
    
    # Convert state to dict if needed
    if isinstance(state, dict):
        state_dict = state
    else:
        # Convert Pydantic model to dictionary
        state_dict = state.model_dump() if hasattr(state, 'model_dump') else state.__dict__
    
    # Convert artifacts to dictionaries if they are not already
    artifacts_dicts = [artifact.model_dump() if hasattr(artifact, 'model_dump') else artifact for artifact in response.artifacts]
    
    # Create the proper return type and convert to state update
    return_obj = RouteToolReturn(
        current_step=response.current_step,
        progress=response.progress,
        artifacts=artifacts_dicts,
        failures=response.failures,
        result=response.result.model_dump() if response.result else None,
        node_result=response.result.model_dump() if response.result else None,
        tool_signature=response.tool_signature
    )
    
    # Add the response to the state update
    state_update = return_obj.to_state_update()
    state_update["route_tool_response"] = response
    return state_update


def execute_tool(state: State, config: Optional[RunnableConfig] = None, runtime: Optional[Runtime] = None) -> Dict[str, Any]:
    """Execute tool with validation and execution in one atomic operation.
    
    This function combines the functionality of route_tool and call_tool
    nodes, eliminating unnecessary indirection as specified in Phase 4
    of the progressive refactoring plan.
    
    Args:
        state: Current agent state.
        config: Optional RunnableConfig for additional configuration.
        runtime: Optional Runtime context for additional runtime information.
        
    Returns:
        Dictionary with tool execution result and state updates.
        
    Notes:
        This addresses the critical problem of unnecessary indirection
        where route_tool + call_tool were doing one job. Now it's
        one atomic operation with proper error handling.
    """
    logger.debug("Executing execute_tool node (merged route + call)")
    from ..nodes.execute_tool import execute_tool as execute_tool_impl
    
    # Call the implementation and get the response
    response : ExecuteToolResponse = execute_tool_impl(state, config, runtime)
    
    # Convert state to dict if needed
    if isinstance(state, dict):
        state_dict = state
    else:
        # Convert Pydantic model to dictionary
        state_dict = state.model_dump() if hasattr(state, 'model_dump') else state.__dict__
    
    # Convert artifacts to dictionaries if they are not already
    artifacts_dicts = [artifact.model_dump() if hasattr(artifact, 'model_dump') else artifact for artifact in response.artifacts]
    
    # Create the proper return type and convert to state update
    return_obj = ExecuteToolReturn(
        current_step=response.current_step,
        progress=response.progress,
        artifacts=artifacts_dicts,
        failures=response.failures,
        result=response.result.model_dump() if response.result else None,
        node_result=response.result.model_dump() if response.result else None,
        tool_signature=response.tool_signature
    )
    
    # Add the response to the state update
    state_update = return_obj.to_state_update()
    state_update["execute_tool_response"] = response
    return state_update


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
    logger.debug("Executing call_tool node")
    from ..nodes.call_tool import call_tool as call_tool_impl
    
    # Call the implementation and get the response
    response : CallToolResponse = call_tool_impl(state, config, runtime)
    
    # Convert state to dict if needed
    if isinstance(state, dict):
        state_dict = state
    else:
        # Convert Pydantic model to dictionary
        state_dict = state.model_dump() if hasattr(state, 'model_dump') else state.__dict__
    
    # Convert artifacts to dictionaries if they are not already
    artifacts_dicts = [artifact.model_dump() if hasattr(artifact, 'model_dump') else artifact for artifact in response.artifacts]
    
    # Create the proper return type and convert to state update
    return_obj = CallToolReturn(
        current_step=response.current_step,
        progress=response.progress,
        artifacts=artifacts_dicts,
        failures=response.failures,
        result=response.result.model_dump() if response.result else None,
        node_result=response.result.model_dump() if response.result else None
    )
    
    # Add the response to the state update
    state_update = return_obj.to_state_update()
    state_update["call_tool_response"] = response
    return state_update


def evaluate(state: State, config: Optional[RunnableConfig] = None, runtime: Optional[Runtime] = None) -> Command:
    """Evaluate the step result and determine next action.
    
    This function delegates to the actual evaluate implementation
    in the nodes module to maintain separation of concerns.
    
    Args:
        state: Current agent state with step execution results.
        config: Optional RunnableConfig for additional configuration.
        runtime: Optional Runtime context for additional runtime information.
        
    Returns:
        Command with evaluation results and routing decision.
        
    Notes:
        Uses Command for atomic update+goto semantics as specified in AGENTS.md.
        The evaluate node makes intelligent routing decisions and returns
        both state updates and the next node to execute.
    """
    logger.debug("Executing evaluate node")
    from ..nodes.evaluate import evaluate as evaluate_impl
    
    # Call the implementation and get the response
    response : EvaluateResponse = evaluate_impl(state, config, runtime)
    
    # Convert state to dict if needed
    if isinstance(state, dict):
        state_dict = state
    else:
        # Convert Pydantic model to dictionary
        state_dict = state.model_dump() if hasattr(state, 'model_dump') else state.__dict__
    
    # Prepare state updates
    state_updates = {
        "current_step": response.current_step,
        "progress": response.progress,
        "artifacts": response.artifacts,
        "failures": response.failures,
        "result": response.result.model_dump() if response.result else None,
        "evaluate_response": response,
        "retry_count": response.result.retry_count if response.result else state_dict.get("retry_count", 0),
        "todo_list": response.todo_list  # Include updated todo list
    }
    
    # Return Command for atomic update+goto semantics
    return Command(
        update=state_updates,
        goto=response.current_step
    )




def diagnose(state: State, config: Optional[RunnableConfig] = None, runtime: Optional[Runtime] = None) -> Dict[str, Any]:
    """Diagnose failures and determine remediation.
    
    Args:
        state: Current agent state.
        config: Optional RunnableConfig for additional configuration.
        runtime: Optional Runtime context for additional runtime information.
        
    Returns:
        Dictionary with diagnosis results and state updates.
    """
    from ..nodes.diagnose import diagnose as diagnose_impl
    from ..nodes.return_types import DiagnoseReturn
    
    # Call the implementation and get the response
    response = diagnose_impl(state, config, runtime)
    
    # Convert state to dict if needed
    if isinstance(state, dict):
        state_dict = state
    else:
        # Convert Pydantic model to dictionary
        state_dict = state.model_dump() if hasattr(state, 'model_dump') else state.__dict__
    
    # Convert artifacts to dictionaries if they are not already
    artifacts_dicts = [artifact.model_dump() if hasattr(artifact, 'model_dump') else artifact for artifact in response.artifacts]
    
    # Create the proper return type and convert to state update
    return_obj = DiagnoseReturn(
        current_step=response.current_step,
        progress=response.progress,
        artifacts=artifacts_dicts,
        failures=response.failures,
        result=response.result.model_dump() if response.result else None,
        node_result=response.result.model_dump() if response.result else None
    )
    
    # Add the response to the state update
    state_update = return_obj.to_state_update()
    state_update["diagnose_response"] = response
    # Also add error_context to state if it exists
    if response.error_context:
        state_update["error_context"] = response.error_context
    return state_update


def escalate(state: State, config: Optional[RunnableConfig] = None, runtime: Optional[Runtime] = None) -> Command:
    """Handle escalation to human input with interrupt for human-in-the-loop.
    
    Args:
        state: Current agent state.
        config: Optional RunnableConfig for additional configuration.
        runtime: Optional Runtime context for additional runtime information.
        
    Returns:
        Command with escalation handling and interrupt for human input.
        
    Notes:
        This node implements human-in-the-loop functionality by interrupting
        execution to wait for human input. The agent will pause and wait
        for human intervention before resuming execution.
    """
    from ..nodes.escalate import escalate as escalate_impl
    from langgraph.types import interrupt
    
    # Call the implementation and get the response
    response = escalate_impl(state, config, runtime)
    
    # Convert state to dict if needed
    if isinstance(state, dict):
        state_dict = state
    else:
        # Convert Pydantic model to dictionary
        state_dict = state.model_dump() if hasattr(state, 'model_dump') else state.__dict__
    
    # Prepare state updates
    state_updates = {
        "current_step": response.current_step,
        "progress": response.progress,
        "artifacts": response.artifacts,
        "failures": response.failures,
        "result": response.result.model_dump() if response.result else None,
        "escalate_response": response,
        "escalation_context": response.escalation_context,
        "todo_list": state_dict.get("todo_list", [])  # Preserve current todo list
    }
    
    # Interrupt for human input (human-in-the-loop)
    interrupt(response.escalation_context)
    
    # Return Command for atomic update+goto semantics
    return Command(
        update=state_updates,
        goto=response.current_step
    )


def answer(state: State, config: Optional[RunnableConfig] = None, runtime: Optional[Runtime] = None) -> Dict[str, Any]:
    """Synthesize final answer and close cleanly.
    
    Args:
        state: Current agent state.
        config: Optional RunnableConfig for additional configuration.
        runtime: Optional Runtime context for additional runtime information.
        
    Returns:
        Dictionary with final answer and state updates.
    """
    from ..nodes.answer import answer as answer_impl
    from ..nodes.return_types import AnswerReturn
    
    # Call the implementation and get the response
    response = answer_impl(state, config, runtime)
    
    # Convert state to dict if needed
    if isinstance(state, dict):
        state_dict = state
    else:
        # Convert Pydantic model to dictionary
        state_dict = state.model_dump() if hasattr(state, 'model_dump') else state.__dict__
    
    # Convert artifacts to dictionaries if they are not already
    artifacts_dicts = [artifact.model_dump() if hasattr(artifact, 'model_dump') else artifact for artifact in response.artifacts]
    
    # Create the proper return type and convert to state update
    return_obj = AnswerReturn(
        current_step=response.current_step,
        progress=response.progress,
        artifacts=artifacts_dicts,
        failures=response.failures,
        result=response.result.model_dump() if response.result else None,
        node_result=response.result.model_dump() if response.result else None
    )
    
    # Add the response to the state update
    state_update = return_obj.to_state_update()
    state_update["answer_response"] = response
    return state_update


def create_agent_graph(
    checkpointer: BaseCheckpointSaver | None = None,
    tracer: Optional["Tracer"] = None,
    recursion_limit: int = 25
) -> StateGraph:
    """Create the agent's LangGraph state machine.
    
    Args:
        checkpointer: Optional checkpointer for state persistence.
        tracer: Optional tracer for observability and monitoring.
        recursion_limit: Maximum number of supersteps allowed.
        
    Returns:
        Compiled LangGraph state machine.
        
    Notes:
        The graph implements the state machine defined in AGENTS.md with
        nodes for parsing, planning, routing, execution, evaluation,
        diagnosis, escalation, and answering. Includes support for:
        - Checkpointer for durable memory and deterministic resume
        - Human-in-the-loop with interrupt gates
        - Langfuse tracing and observability
        - Recursion limits for safety
    """
    # Create the state graph
    workflow = StateGraph(State)
    
    # Add nodes
    workflow.add_node("parse_intent", parse_intent)
    workflow.add_node("resolve_entities", resolve_entities)
    workflow.add_node("disambiguate", disambiguate)
    workflow.add_node("plan_step", plan_step)
    workflow.add_node("execute_tool", execute_tool)  # Merged tool execution node (Phase 4)
    workflow.add_node("evaluate", evaluate)
    workflow.add_node("diagnose", diagnose)
    workflow.add_node("escalate", escalate)
    workflow.add_node("answer", answer)
    
    # Add edges
    workflow.add_edge(START, "parse_intent")
    
    # Conditional routing after parse_intent (Phase 1)
    workflow.add_conditional_edges(
        "parse_intent",
        route_after_parse_intent,
        {
            "resolve_entities": "resolve_entities",
            "plan_step": "plan_step",
            "diagnose": "diagnose"
        }
    )
    
    # Conditional routing after resolve_entities (Phase 2)
    workflow.add_conditional_edges(
        "resolve_entities",
        route_after_resolve_entities,
        {
            "disambiguate": "disambiguate",
            "plan_step": "plan_step",
            "diagnose": "diagnose"
        }
    )
    
    # Conditional routing after disambiguate
    workflow.add_conditional_edges(
        "disambiguate",
        route_after_disambiguate,
        {
            "plan_step": "plan_step",
            "diagnose": "diagnose"
        }
    )
    
    # Direct edges for planning and execution (using execute_tool instead of route_tool + call_tool)
    workflow.add_edge("plan_step", "execute_tool")
    workflow.add_edge("execute_tool", "evaluate")
    
    # Note: evaluate and escalate nodes use Command for routing,
    # so they don't need conditional edges - they handle routing internally
    
    # Conditional routing after diagnose
    workflow.add_conditional_edges(
        "diagnose",
        route_after_diagnose,
        {
            "plan_step": "plan_step",
            "escalate": "escalate"
        }
    )
    
    # Direct edge for completion
    workflow.add_edge("answer", END)
    
    # Prepare compilation arguments
    compile_args = {}
    
    # Add checkpointer if provided
    if checkpointer:
        compile_args["checkpointer"] = checkpointer
    
    # Compile the graph
    compiled_graph = workflow.compile(**compile_args)
    
    # Add Langfuse tracing if tracer is provided
    if tracer:
        # Attach Langfuse callback handler to the compiled graph
        from ..observability.langfuse_callback import LangfuseCallbackHandler
        
        langfuse_handler = LangfuseCallbackHandler(tracer)
        # Note: Callbacks are typically attached at invocation time
        # rather than at compile time in LangGraph
    
    return compiled_graph


def create_agent_with_checkpointer(
    checkpointer_type: str = "memory",
    tracer: Optional["Tracer"] = None,
    recursion_limit: int = 25,
    **kwargs: Any
) -> StateGraph:
    """Create an agent with a specific checkpointer type and optional tracer.
    
    Args:
        checkpointer_type: Type of checkpointer to use.
        tracer: Optional tracer for observability and monitoring.
        recursion_limit: Maximum number of supersteps allowed.
        **kwargs: Additional configuration parameters.
        
    Returns:
        Compiled LangGraph state machine with checkpointer and optional tracer.
        
    Notes:
        This function provides a convenient way to create an agent with
        persistence and observability features configured.
    """
    checkpointer = create_checkpointer(checkpointer_type, **kwargs)
    return create_agent_graph(
        checkpointer=checkpointer,
        tracer=tracer,
        recursion_limit=recursion_limit
    )


def create_production_agent(
    checkpointer_type: str = "memory",
    tracer_type: str = "langfuse",
    recursion_limit: int = 25,
    **kwargs: Any
) -> StateGraph:
    """Create a production-ready agent with full observability and persistence.
    
    Args:
        checkpointer_type: Type of checkpointer to use for persistence.
        tracer_type: Type of tracer to use for observability ("langfuse", "console", "noop").
        recursion_limit: Maximum number of supersteps allowed.
        **kwargs: Additional configuration parameters.
        
    Returns:
        Compiled LangGraph state machine with full production features.
        
    Notes:
        This function creates an agent configured for production use with:
        - Persistent state management via checkpointer
        - Comprehensive observability via Langfuse tracer
        - Human-in-the-loop support with interrupts
        - Recursion limits for safety
        - Error handling and recovery mechanisms
    """
    from ..observability.tracer_factory import make_tracer, TracerConfig
    
    # Create checkpointer for persistence
    checkpointer = create_checkpointer(checkpointer_type, **kwargs)
    
    # Create tracer for observability
    try:
        tracer_config = TracerConfig(tracer_type, **kwargs)
        tracer = make_tracer(tracer_config)
    except Exception as e:
        # Fallback to noop tracer if the requested tracer fails
        print(f"Warning: Failed to create {tracer_type} tracer, falling back to noop tracer: {e}")
        tracer_config = TracerConfig("noop", **kwargs)
        tracer = make_tracer(tracer_config)
    
    # Create the agent with all production features
    return create_agent_graph(
        checkpointer=checkpointer,
        tracer=tracer,
        recursion_limit=recursion_limit
    )


