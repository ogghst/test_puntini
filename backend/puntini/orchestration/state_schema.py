"""State schema definition for the agent.

This module defines the TypedDict state schema for the LangGraph state machine,
ensuring proper state management with reducers to prevent unbounded growth.
"""

from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict, Annotated
from operator import add

from ..nodes.message import (
    Artifact, Failure, ErrorContext, EscalateContext,
    ParseGoalResponse, PlanStepResponse, RouteToolResponse, 
    CallToolResponse, EvaluateResponse, DiagnoseResponse, 
    EscalateResponse, AnswerResponse
)
from ..nodes.plan_step import StepPlan


class State(TypedDict):
    """TypedDict state schema for the agent.
    
    The state contains all necessary information for the agent's execution
    including the goal, plan, progress, failures, messages, and components.
    Uses TypedDict with reducers to prevent unbounded growth as specified in AGENTS.md.
    """
    
    # Core goal and planning
    goal: str  # The user's goal or request
    plan: Annotated[List[str], add]  # Execution plan steps (append-only)
    progress: Annotated[List[str], add]  # Progress messages (append-only)
    
    # Error handling and retry management
    failures: Annotated[List[Failure], add]  # List of failures (append-only)
    retry_count: int  # Current retry count
    max_retries: int  # Maximum retry count
    
    # Communication and context
    messages: Annotated[List[Any], add]  # Communication messages (append-only)
    current_step: str  # Current execution step
    current_attempt: int  # Current attempt number
    
    # Results and artifacts
    artifacts: Annotated[List[Artifact], add]  # Artifacts created during execution (append-only)
    result: Optional[Dict[str, Any]]  # Current execution result
    
    # Agent components (shared across all nodes)
    tool_registry: Optional[Any]  # Tool registry instance
    graph_store: Optional[Any]  # Graph store instance
    context_manager: Optional[Any]  # Context manager instance
    tracer: Optional[Any]  # Tracer instance
    
    # Private channels for inter-node data
    tool_signature: Optional[Dict[str, Any]]  # Tool signature for execution
    error_context: Optional[ErrorContext]  # Error context for diagnosis
    escalation_context: Optional[EscalateContext]  # Escalation context
    
    # Node responses for type safety
    parse_goal_response: Optional[ParseGoalResponse]  # Parse goal node response
    plan_step_response: Optional[PlanStepResponse]  # Plan step node response
    route_tool_response: Optional[RouteToolResponse]  # Route tool node response
    call_tool_response: Optional[CallToolResponse]  # Call tool node response
    evaluate_response: Optional[EvaluateResponse]  # Evaluate node response
    diagnose_response: Optional[DiagnoseResponse]  # Diagnose node response
    escalate_response: Optional[EscalateResponse]  # Escalate node response
    answer_response: Optional[AnswerResponse]  # Answer node response
