"""Minimal state pattern for Phase 3 of progressive refactoring.

This module implements the minimal state pattern as specified in Phase 3 of the
progressive refactoring plan, addressing the state bloat and information overload
problems identified in the graph critics analysis.

The minimal state pattern reduces state complexity by:
1. Keeping only essential shared state in the main State
2. Using node-specific contexts for node-specific data
3. Eliminating duplicate state storage
4. Improving data flow clarity

This addresses the critical problems identified in the graph critics:
- State bloat: Passing everything through every node
- Information overload: Nodes receive data they don't need
- Tight coupling: All nodes depend on the full state schema
- Memory inefficiency: Dragging full history through every node
"""

from typing import Any, Dict, Generic, TypeVar, Optional, Union
from typing_extensions import TypedDict, Annotated
from dataclasses import dataclass
from operator import add

from ..models.goal_schemas import TodoItem
from ..models.intent_schemas import IntentSpec, ResolvedGoalSpec
from ..nodes.message import Artifact, Failure, ErrorContext, EscalateContext

T = TypeVar('T')


class Services(TypedDict):
    """Shared services registry for the agent.
    
    This contains all the services that nodes need access to,
    avoiding the need to pass them through the state.
    """
    tool_registry: Any
    context_manager: Any
    tracer: Any
    graph_store: Any


class MinimalState(TypedDict):
    """Minimal state schema following the minimal state pattern.
    
    This addresses the state bloat problem by keeping only essential
    shared state and moving node-specific data to node contexts.
    
    Fields:
        session_id: Unique identifier for the session
        current_node: Current executing node name
        shared_services: Registry of shared services
        goal: The user's goal or request (shared across nodes)
        messages: Communication messages (append-only)
        artifacts: Artifacts created during execution (append-only)
        failures: Failures encountered (append-only)
        progress: Progress messages (append-only)
        todo_list: List of todos for goal execution
        retry_count: Current retry count
        max_retries: Maximum retry count
    """
    session_id: str
    current_node: str
    shared_services: Services
    
    # Core shared state
    goal: str
    messages: Annotated[list[Any], add]
    artifacts: Annotated[list[Artifact], add]
    failures: Annotated[list[Failure], add]
    progress: Annotated[list[str], add]
    todo_list: list[TodoItem]
    
    # Retry management
    retry_count: int
    max_retries: int


class NodeInput(Generic[T]):
    """Generic node input with minimal state and node-specific context.
    
    This implements the node-specific context pattern where each node
    receives only the minimal shared state plus its specific context.
    
    Args:
        state: Minimal shared state
        context: Node-specific context data
    """
    def __init__(self, state: MinimalState, context: T):
        self.state = state
        self.context = context


@dataclass
class ParseGoalInput:
    """Node-specific context for parse_goal node.
    
    Contains only the data needed for parsing goals, avoiding
    information overload identified in the graph critics analysis.
    """
    raw_goal: str
    user_context: Optional[Dict[str, Any]] = None
    previous_attempts: Optional[list[str]] = None


@dataclass
class PlanStepInput:
    """Node-specific context for plan_step node.
    
    Contains only the data needed for planning steps, including
    the resolved goal specification and graph context.
    """
    goal_spec: Optional[ResolvedGoalSpec] = None
    intent_spec: Optional[IntentSpec] = None
    graph_snapshot: Optional[Dict[str, Any]] = None
    previous_results: Optional[list[Dict[str, Any]]] = None
    current_step_number: int = 1


@dataclass
class ResolveEntitiesInput:
    """Node-specific context for resolve_entities node.
    
    Contains only the data needed for entity resolution with
    graph context as specified in Phase 2 of the refactoring plan.
    """
    intent_spec: IntentSpec
    graph_context: Optional[Dict[str, Any]] = None
    entity_candidates: Optional[list[Dict[str, Any]]] = None


@dataclass
class ExecuteToolInput:
    """Node-specific context for execute_tool node.
    
    Contains only the data needed for tool execution, combining
    the functionality of route_tool and call_tool nodes.
    """
    tool_signature: Dict[str, Any]
    validation_result: Optional[Dict[str, Any]] = None
    execution_context: Optional[Dict[str, Any]] = None


@dataclass
class EvaluateInput:
    """Node-specific context for evaluate node.
    
    Contains only the data needed for evaluation and routing decisions.
    """
    execution_result: Dict[str, Any]
    step_plan: Optional[Dict[str, Any]] = None
    goal_completion_status: Optional[bool] = None


@dataclass
class DiagnoseInput:
    """Node-specific context for diagnose node.
    
    Contains only the data needed for error diagnosis and classification.
    """
    error_context: ErrorContext
    failure_history: Optional[list[Failure]] = None
    retry_context: Optional[Dict[str, Any]] = None


@dataclass
class EscalateInput:
    """Node-specific context for escalate node.
    
    Contains only the data needed for escalation and human-in-the-loop.
    """
    escalation_context: EscalateContext
    escalation_reason: str
    user_input_required: bool = True


@dataclass
class AnswerInput:
    """Node-specific context for answer node.
    
    Contains only the data needed for synthesizing final answers.
    """
    final_result: Dict[str, Any]
    summary_context: Optional[Dict[str, Any]] = None
    completion_status: str = "success"


def create_node_input(state: MinimalState, context: T) -> NodeInput[T]:
    """Create a node input with minimal state and node-specific context.
    
    Args:
        state: Minimal shared state
        context: Node-specific context
        
    Returns:
        NodeInput with the provided state and context
        
    Notes:
        This function provides a clean way to create node inputs
        following the minimal state pattern.
    """
    return NodeInput(state, context)


def extract_minimal_state(full_state: Dict[str, Any]) -> MinimalState:
    """Extract minimal state from a full state dictionary.
    
    Args:
        full_state: Full state dictionary from the current implementation
        
    Returns:
        MinimalState with only essential shared fields
        
    Notes:
        This function helps migrate from the current bloated state
        to the minimal state pattern during the refactoring process.
    """
    return MinimalState(
        session_id=full_state.get("session_id", "default"),
        current_node=full_state.get("current_node", "unknown"),
        shared_services=Services(
            tool_registry=full_state.get("tool_registry"),
            context_manager=full_state.get("context_manager"),
            tracer=full_state.get("tracer"),
            graph_store=full_state.get("graph_store")
        ),
        goal=full_state.get("goal", ""),
        messages=full_state.get("messages", []),
        artifacts=full_state.get("artifacts", []),
        failures=full_state.get("failures", []),
        progress=full_state.get("progress", []),
        todo_list=full_state.get("todo_list", []),
        retry_count=full_state.get("retry_count", 0),
        max_retries=full_state.get("max_retries", 3)
    )


def merge_node_output(minimal_state: MinimalState, node_output: Dict[str, Any]) -> MinimalState:
    """Merge node output back into minimal state.
    
    Args:
        minimal_state: Current minimal state
        node_output: Output from a node execution
        
    Returns:
        Updated minimal state with node output merged
        
    Notes:
        This function handles the merging of node outputs back into
        the minimal state, applying reducers as needed.
    """
    # Create a copy of the minimal state
    updated_state = minimal_state.copy()
    
    # Apply updates using reducers
    for key, value in node_output.items():
        # Apply reducer if the field has one
        if key in ["messages", "artifacts", "failures", "progress"]:
            # These fields use append reducers
            current_value = updated_state.get(key, [])
            if isinstance(current_value, list) and isinstance(value, list):
                updated_state[key] = current_value + value
            else:
                updated_state[key] = value
        else:
            # Direct assignment for other fields (including new fields like 'result')
            updated_state[key] = value
    
    return updated_state
