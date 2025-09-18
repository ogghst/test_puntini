"""State schema definition for the agent.

This module defines the Pydantic state schema for the LangGraph state machine,
ensuring proper state management and validation.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict

from ..nodes.message import (
    Artifact, Failure, ErrorContext, EscalateContext,
    ParseGoalResponse, PlanStepResponse, RouteToolResponse, 
    CallToolResponse, EvaluateResponse, DiagnoseResponse, 
    EscalateResponse, AnswerResponse
)
from ..nodes.plan_step import StepPlan


class State(BaseModel):
    """Pydantic state schema for the agent.
    
    The state contains all necessary information for the agent's execution
    including the goal, plan, progress, failures, messages, and components.
    Uses Pydantic for robust validation and type safety.
    """
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    # Core goal and planning
    goal: str = Field(description="The user's goal or request")
    plan: List[str] = Field(default_factory=list, description="Execution plan steps")
    progress: List[str] = Field(default_factory=list, description="Progress messages")
    
    # Error handling and retry management
    failures: List[Failure] = Field(default_factory=list, description="List of failures that occurred")
    retry_count: int = Field(default=0, description="Current retry count")
    max_retries: int = Field(default=3, description="Maximum retry count")
    
    # Communication and context
    messages: List[Any] = Field(default_factory=list, description="Communication messages")
    current_step: str = Field(default="parse_goal", description="Current execution step")
    current_attempt: int = Field(default=1, description="Current attempt number")
    
    # Results and artifacts
    artifacts: List[Artifact] = Field(default_factory=list, description="Artifacts created during execution")
    result: Optional[Dict[str, Any]] = Field(default=None, description="Current execution result")
    
    # Agent components (shared across all nodes)
    tool_registry: Optional[Any] = Field(default=None, description="Tool registry instance")
    graph_store: Optional[Any] = Field(default=None, description="Graph store instance")
    context_manager: Optional[Any] = Field(default=None, description="Context manager instance")
    tracer: Optional[Any] = Field(default=None, description="Tracer instance")
    
    # Private channels for inter-node data
    tool_signature: Optional[Dict[str, Any]] = Field(default=None, description="Tool signature for execution")
    error_context: Optional[ErrorContext] = Field(default=None, description="Error context for diagnosis")
    escalation_context: Optional[EscalateContext] = Field(default=None, description="Escalation context")
    
    # Node responses for type safety
    parse_goal_response: Optional[ParseGoalResponse] = Field(default=None, description="Parse goal node response")
    plan_step_response: Optional[PlanStepResponse] = Field(default=None, description="Plan step node response")
    route_tool_response: Optional[RouteToolResponse] = Field(default=None, description="Route tool node response")
    call_tool_response: Optional[CallToolResponse] = Field(default=None, description="Call tool node response")
    evaluate_response: Optional[EvaluateResponse] = Field(default=None, description="Evaluate node response")
    diagnose_response: Optional[DiagnoseResponse] = Field(default=None, description="Diagnose node response")
    escalate_response: Optional[EscalateResponse] = Field(default=None, description="Escalate node response")
    answer_response: Optional[AnswerResponse] = Field(default=None, description="Answer node response")


# Rebuild the model to resolve forward references
State.model_rebuild()
