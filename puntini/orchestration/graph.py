"""LangGraph state machine definition.

This module defines the main LangGraph state machine with nodes, edges,
and conditional routing for the agent's execution flow.
"""

from typing import Any, Dict, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.types import Command

from .state import State
from .checkpointer import create_checkpointer, get_checkpoint_config


def route_after_parse_goal(state: State) -> str:
    """Route after parsing goal based on complexity and parsing results.
    
    Args:
        state: Current agent state with parsed goal information.
        
    Returns:
        The next node to execute.
    """
    result = state.get("result", {})
    
    # If parsing failed, route to diagnose
    if result.get("status") == "error":
        return "diagnose"
    
    # If parsing succeeded, use the determined next step
    return state.get("current_step", "plan_step")


def route_after_evaluate(state: State) -> str:
    """Route after evaluation based on step results.
    
    Args:
        state: Current agent state with evaluation results.
        
    Returns:
        The next node to execute.
    """
    result = state.get("result", {})
    status = result.get("status", "unknown")
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 3)
    
    if status == "success":
        # Check if goal is complete
        if result.get("goal_complete", False):
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
    result = state.get("result", {})
    error_context = state.get("_error_context", {})
    
    error_type = error_context.get("type", "unknown")
    
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


def parse_goal(state: State) -> Dict[str, Any]:
    """Parse the goal and extract structured information.
    
    This function delegates to the actual parse_goal implementation
    in the nodes module to maintain separation of concerns.
    
    Args:
        state: Current agent state.
        
    Returns:
        Updated state with parsed goal information.
    """
    from ..nodes.parse_goal import parse_goal as parse_goal_impl
    return parse_goal_impl(state)


def plan_step(state: State) -> Dict[str, Any]:
    """Plan the next step in the agent's execution.
    
    Args:
        state: Current agent state.
        
    Returns:
        Updated state with planned step.
    """
    # TODO: Implement step planning logic
    return {
        "current_step": "route_tool",
        "_tool_signature": {"name": "example_tool", "args": {}}
    }


def route_tool(state: State) -> Dict[str, Any]:
    """Route to the appropriate tool or branch.
    
    Args:
        state: Current agent state.
        
    Returns:
        Updated state with routing decision.
    """
    # TODO: Implement tool routing logic
    return {
        "current_step": "call_tool"
    }


def call_tool(state: State) -> Dict[str, Any]:
    """Execute the selected tool.
    
    Args:
        state: Current agent state.
        
    Returns:
        Updated state with tool execution result.
    """
    # TODO: Implement tool execution logic
    return {
        "current_step": "evaluate",
        "result": {"status": "success", "data": {}}
    }


def evaluate(state: State) -> Command:
    """Evaluate the step result and decide next action.
    
    Args:
        state: Current agent state.
        
    Returns:
        Command with next node and state updates.
    """
    # TODO: Implement evaluation logic
    if state.get("result", {}).get("status") == "success":
        return Command(update={"current_step": "answer"}, goto="answer")
    else:
        return Command(update={"current_step": "diagnose"}, goto="diagnose")


def diagnose(state: State) -> Dict[str, Any]:
    """Diagnose failures and determine remediation.
    
    Args:
        state: Current agent state.
        
    Returns:
        Updated state with diagnosis results.
    """
    # TODO: Implement diagnosis logic
    return {
        "current_step": "escalate",
        "_error_context": {"type": "systematic", "message": "Unknown error"}
    }


def escalate(state: State) -> Command:
    """Handle escalation to human input.
    
    Args:
        state: Current agent state.
        
    Returns:
        Command with escalation handling.
    """
    # TODO: Implement escalation logic
    return Command(update={"current_step": "answer"}, goto="answer")


def answer(state: State) -> Dict[str, Any]:
    """Synthesize final answer and close cleanly.
    
    Args:
        state: Current agent state.
        
    Returns:
        Updated state with final answer.
    """
    # TODO: Implement answer synthesis logic
    return {
        "current_step": "complete",
        "result": {"answer": "Task completed successfully"}
    }


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
