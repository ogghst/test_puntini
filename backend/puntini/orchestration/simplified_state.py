"""Simplified state schema implementing Phase 3 minimal state pattern.

This module implements the simplified state schema as specified in Phase 3
of the progressive refactoring plan, addressing the state bloat and complexity
issues identified in the graph critics analysis.

Key improvements:
1. Minimal shared state with only essential fields
2. Node-specific contexts for node-specific data
3. Elimination of duplicate state storage
4. Clear separation between shared and private data
5. Improved data flow and reduced coupling

This addresses the critical problems:
- State bloat: Reduced from 75+ fields to ~15 essential fields
- Information overload: Nodes receive only what they need
- Tight coupling: Clear separation of concerns
- Memory inefficiency: Minimal state footprint
"""

from typing import Any, Dict, List, Optional, Union
from typing_extensions import TypedDict, Annotated
from operator import add

from .minimal_state import MinimalState, Services, NodeInput
from ..models.goal_schemas import TodoItem
from ..models.intent_schemas import IntentSpec, ResolvedGoalSpec
from ..nodes.message import Artifact, Failure, ErrorContext, EscalateContext


class SimplifiedState(TypedDict):
    """Simplified state schema implementing the minimal state pattern.
    
    This state schema addresses the state bloat problem by keeping only
    essential shared state and moving node-specific data to contexts.
    
    Fields:
        session_id: Unique session identifier
        current_node: Currently executing node
        shared_services: Registry of shared services
        goal: User's goal or request
        messages: Communication messages (append-only)
        artifacts: Execution artifacts (append-only)
        failures: Execution failures (append-only)
        progress: Progress messages (append-only)
        todo_list: List of todos for goal execution
        retry_count: Current retry count
        max_retries: Maximum retry attempts
        result: Current execution result
        current_step: Current execution step name
        current_attempt: Current attempt number
    """
    # Session and execution tracking
    session_id: str
    current_node: str
    shared_services: Services
    
    # Core shared state
    goal: str
    messages: Annotated[List[Any], add]
    artifacts: Annotated[List[Artifact], add]
    failures: Annotated[List[Failure], add]
    progress: Annotated[List[str], add]
    todo_list: List[TodoItem]
    
    # Execution control
    retry_count: int
    max_retries: int
    result: Optional[Dict[str, Any]]
    current_step: str
    current_attempt: int


# Type aliases for backward compatibility during migration
State = SimplifiedState
MinimalStateType = MinimalState


def create_simplified_state(
    session_id: str = "default",
    goal: str = "",
    shared_services: Optional[Services] = None,
    **kwargs: Any
) -> SimplifiedState:
    """Create a new simplified state instance.
    
    Args:
        session_id: Unique session identifier
        goal: User's goal or request
        shared_services: Registry of shared services
        **kwargs: Additional state fields
        
    Returns:
        New SimplifiedState instance with default values
        
    Notes:
        This function provides a clean way to create new state instances
        with proper defaults and type safety.
    """
    if shared_services is None:
        shared_services = Services(
            tool_registry=None,
            context_manager=None,
            tracer=None,
            graph_store=None
        )
    
    return SimplifiedState(
        session_id=session_id,
        current_node="start",
        shared_services=shared_services,
        goal=goal,
        messages=kwargs.get("messages", []),
        artifacts=kwargs.get("artifacts", []),
        failures=kwargs.get("failures", []),
        progress=kwargs.get("progress", []),
        todo_list=kwargs.get("todo_list", []),
        retry_count=kwargs.get("retry_count", 0),
        max_retries=kwargs.get("max_retries", 3),
        result=kwargs.get("result"),
        current_step=kwargs.get("current_step", "start"),
        current_attempt=kwargs.get("current_attempt", 1)
    )


def migrate_from_bloated_state(bloated_state: Dict[str, Any]) -> SimplifiedState:
    """Migrate from the current bloated state to simplified state.
    
    Args:
        bloated_state: Current bloated state dictionary
        
    Returns:
        SimplifiedState with only essential fields
        
    Notes:
        This function helps migrate from the current implementation
        to the simplified state pattern during the refactoring process.
        It extracts only the essential fields and discards node-specific
        data that should be in node contexts.
    """
    # Extract essential shared fields
    essential_fields = {
        "session_id": bloated_state.get("session_id", "default"),
        "current_node": bloated_state.get("current_node", "start"),
        "shared_services": Services(
            tool_registry=bloated_state.get("tool_registry"),
            context_manager=bloated_state.get("context_manager"),
            tracer=bloated_state.get("tracer"),
            graph_store=bloated_state.get("graph_store")
        ),
        "goal": bloated_state.get("goal", ""),
        "messages": bloated_state.get("messages", []),
        "artifacts": bloated_state.get("artifacts", []),
        "failures": bloated_state.get("failures", []),
        "progress": bloated_state.get("progress", []),
        "todo_list": bloated_state.get("todo_list", []),
        "retry_count": bloated_state.get("retry_count", 0),
        "max_retries": bloated_state.get("max_retries", 3),
        "result": bloated_state.get("result"),
        "current_step": bloated_state.get("current_step", "start"),
        "current_attempt": bloated_state.get("current_attempt", 1)
    }
    
    return SimplifiedState(**essential_fields)


def extract_node_context(state: SimplifiedState, node_name: str) -> Dict[str, Any]:
    """Extract node-specific context from simplified state.
    
    Args:
        state: Simplified state instance
        node_name: Name of the node requesting context
        
    Returns:
        Dictionary containing node-specific context
        
    Notes:
        This function provides node-specific context based on the
        current state and node requirements. It implements the
        progressive context disclosure principle.
    """
    context = {
        "session_id": state["session_id"],
        "current_node": node_name,
        "goal": state["goal"],
        "retry_count": state["retry_count"],
        "max_retries": state["max_retries"]
    }
    
    # Add node-specific context based on node type
    if node_name == "parse_intent":
        context.update({
            "raw_goal": state["goal"],
            "previous_attempts": [f["message"] for f in state["failures"][-3:]]
        })
    elif node_name == "resolve_entities":
        context.update({
            "intent_spec": state.get("intent_spec"),
            "graph_context": state.get("graph_context")
        })
    elif node_name == "plan_step":
        context.update({
            "goal_spec": state.get("resolved_goal_spec"),
            "intent_spec": state.get("intent_spec"),
            "current_step_number": len(state["progress"]) + 1
        })
    elif node_name == "execute_tool":
        context.update({
            "tool_signature": state.get("tool_signature"),
            "execution_context": state.get("execution_context")
        })
    elif node_name == "evaluate":
        context.update({
            "execution_result": state.get("result", {}),
            "goal_completion_status": state.get("goal_complete", False)
        })
    elif node_name == "diagnose":
        context.update({
            "error_context": state.get("error_context"),
            "failure_history": state["failures"][-5:]  # Last 5 failures
        })
    elif node_name == "escalate":
        context.update({
            "escalation_context": state.get("escalation_context"),
            "escalation_reason": state.get("escalation_reason", "unknown")
        })
    elif node_name == "answer":
        context.update({
            "final_result": state.get("result", {}),
            "completion_status": state.get("completion_status", "success")
        })
    
    return context


def update_state_with_node_output(
    state: SimplifiedState, 
    node_output: Dict[str, Any], 
    node_name: str
) -> SimplifiedState:
    """Update state with node output, applying appropriate reducers.
    
    Args:
        state: Current simplified state
        node_output: Output from node execution
        node_name: Name of the executing node
        
    Returns:
        Updated simplified state
        
    Notes:
        This function handles the merging of node outputs back into
        the simplified state, applying reducers as specified in the
        state schema definition.
    """
    # Create a copy of the state
    updated_state = state.copy()
    
    # Apply updates using reducers
    for key, value in node_output.items():
        if key in updated_state:
            # Apply reducer based on field type
            if key in ["messages", "artifacts", "failures", "progress"]:
                # These fields use append reducers
                current_value = updated_state.get(key, [])
                if isinstance(current_value, list) and isinstance(value, list):
                    updated_state[key] = current_value + value
                else:
                    updated_state[key] = value
            else:
                # Direct assignment for other fields
                updated_state[key] = value
    
    # Update current node
    updated_state["current_node"] = node_name
    
    return updated_state


# Reducer functions for the simplified state
def add_to_list(existing: List[Any] | None, updates: List[Any] | None) -> List[Any]:
    """Reducer function for adding items to a list.
    
    Args:
        existing: Existing list (None if not present)
        updates: New items to add (None if no updates)
        
    Returns:
        Updated list with new items appended
    """
    if existing is None:
        existing = []
    if updates is None:
        return existing
    return existing + updates


def set_value(existing: Any | None, new_value: Any | None) -> Any:
    """Reducer function for setting a value.
    
    Args:
        existing: Existing value (ignored)
        new_value: New value to set
        
    Returns:
        The new value
    """
    return new_value
