"""Unit tests for the graph nodes."""

import pytest
from puntini.nodes.call_tool import call_tool
from puntini.nodes.evaluate import evaluate
from puntini.nodes.plan_step import plan_step, StepPlan, ToolSignature
from puntini.orchestration.state import State
from unittest.mock import MagicMock


def test_plan_step_fallback():
    """Tests the plan_step node's fallback mechanism."""
    initial_state: State = {
        "goal": "Some goal without parsed artifacts.",
        "plan": [],
        "progress": [],
        "failures": [],
        "retry_count": 0,
        "max_retries": 3,
        "messages": [],
        "current_step": "plan_step",
        "current_attempt": 1,
        "artifacts": [], # No parsed_goal artifact
        "result": {},
        "_tool_signature": {},
        "_error_context": {},
        "_escalation_context": {},
    }

    result_state = plan_step(initial_state)

    assert result_state["current_step"] == "route_tool"
    assert result_state["_tool_signature"]["tool_name"] == "query_graph"
    assert "Fallback planned step: query_graph" in result_state["progress"]


def test_call_tool_success():
    """Tests the call_tool node with a successful tool execution."""
    initial_state: State = {
        "goal": "Add 2 and 3",
        "plan": [],
        "progress": [],
        "failures": [],
        "retry_count": 0,
        "max_retries": 3,
        "messages": [],
        "current_step": "call_tool",
        "current_attempt": 1,
        "artifacts": [],
        "result": {},
        "_tool_signature": {
            "tool_name": "dummy_tool",
            "tool_args": {"a": 2, "b": 3},
        },
        "_error_context": {},
        "_escalation_context": {},
    }

    result_state = call_tool(initial_state)

    assert result_state["result"]["status"] == "success"
    assert result_state["result"]["result"] == 5
    assert "Executed tool: dummy_tool" in result_state["progress"]


def test_call_tool_not_found():
    """Tests the call_tool node when the tool is not found."""
    initial_state: State = {
        "goal": "Add 2 and 3",
        "plan": [],
        "progress": [],
        "failures": [],
        "retry_count": 0,
        "max_retries": 3,
        "messages": [],
        "current_step": "call_tool",
        "current_attempt": 1,
        "artifacts": [],
        "result": {},
        "_tool_signature": {
            "tool_name": "non_existent_tool",
            "tool_args": {"a": 2, "b": 3},
        },
        "_error_context": {},
        "_escalation_context": {},
    }

    result_state = call_tool(initial_state)

    assert result_state["result"]["status"] == "error"
    assert result_state["result"]["error_type"] == "not_found_error"


def test_evaluate_success_goal_not_complete():
    """Tests the evaluate node with a successful result and goal not complete."""
    initial_state: State = {
        "goal": "Some goal",
        "plan": [],
        "progress": [],
        "failures": [],
        "retry_count": 0,
        "max_retries": 3,
        "messages": [],
        "current_step": "evaluate",
        "current_attempt": 1,
        "artifacts": [],
        "result": {
            "status": "success",
            "goal_complete": False,
        },
        "_tool_signature": {},
        "_error_context": {},
        "_escalation_context": {},
    }

    result_state = evaluate(initial_state)

    assert result_state["result"]["status"] == "success"
    assert not result_state["result"]["goal_complete"]


def test_evaluate_success_goal_complete():
    """Tests the evaluate node with a successful result and goal complete."""
    initial_state: State = {
        "goal": "Some goal",
        "plan": [],
        "progress": [],
        "failures": [],
        "retry_count": 0,
        "max_retries": 3,
        "messages": [],
        "current_step": "evaluate",
        "current_attempt": 1,
        "artifacts": [],
        "result": {
            "status": "success",
            "goal_complete": True,
        },
        "_tool_signature": {},
        "_error_context": {},
        "_escalation_context": {},
    }

    result_state = evaluate(initial_state)

    assert result_state["result"]["status"] == "success"
    assert result_state["result"]["goal_complete"]


def test_evaluate_error():
    """Tests the evaluate node with an error result."""
    initial_state: State = {
        "goal": "Some goal",
        "plan": [],
        "progress": [],
        "failures": [],
        "retry_count": 0,
        "max_retries": 3,
        "messages": [],
        "current_step": "evaluate",
        "current_attempt": 1,
        "artifacts": [],
        "result": {
            "status": "error",
        },
        "_tool_signature": {},
        "_error_context": {},
        "_escalation_context": {},
    }

    result_state = evaluate(initial_state)

    assert result_state["result"]["status"] == "error"
    assert result_state["retry_count"] == 1
