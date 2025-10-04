"""Streamlined message classes for node outputs using generic response wrapper.

This module implements the streamlined response architecture by eliminating
redundant response patterns and using a generic response wrapper with
node-specific result types as specified in Phase 6 of the refactoring plan.
"""

from typing import Any, Dict, List, Optional, Generic, TypeVar, Union
from pydantic import BaseModel, Field
from datetime import datetime

from ..models.goal_schemas import TodoItem, GoalSpec


# Base classes for streamlined architecture
class Artifact(BaseModel):
    """Represents an artifact created during node execution."""
    type: str = Field(description="Type of artifact (e.g., 'parsed_goal', 'tool_execution')")
    data: Dict[str, Any] = Field(description="Artifact data")


class Failure(BaseModel):
    """Represents a failure that occurred during execution."""
    step: str = Field(description="The step where the failure occurred")
    error: str = Field(description="Error message")
    attempt: int = Field(description="Attempt number when failure occurred")
    error_type: str = Field(description="Type of error (e.g., 'validation_error', 'network_error')")
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow, description="When the failure occurred")


class ErrorContext(BaseModel):
    """Context information for error handling."""
    type: str = Field(description="Type of error context")
    message: str = Field(description="Error message")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional error details")


# Node-specific result types (focused and without redundant wrapper fields)
class ParseGoalResult(BaseModel):
    """Result from parse_goal node execution."""
    status: str = Field(description="Execution status: 'success' or 'error'")
    error: Optional[str] = Field(default=None, description="Error message if status is 'error'")
    error_type: Optional[str] = Field(default=None, description="Type of error if status is 'error'")
    
    parsed_goal: Optional[Dict[str, Any]] = Field(default=None, description="Parsed goal data")
    complexity: Optional[str] = Field(default=None, description="Goal complexity level")
    requires_graph_ops: Optional[bool] = Field(default=None, description="Whether goal requires graph operations")
    is_simple: Optional[bool] = Field(default=None, description="Whether goal is simple")
    retryable: Optional[bool] = Field(default=None, description="Whether error is retryable")


class PlanStepResult(BaseModel):
    """Result from plan_step node execution."""
    status: str = Field(description="Execution status: 'success' or 'error'")
    error: Optional[str] = Field(default=None, description="Error message if status is 'error'")
    error_type: Optional[str] = Field(default=None, description="Type of error if status is 'error'")
    
    step_plan: Optional[Dict[str, Any]] = Field(default=None, description="Generated step plan")
    is_final_step: Optional[bool] = Field(default=None, description="Whether this is the final step")
    overall_progress: Optional[float] = Field(default=None, description="Overall progress towards goal")


class ExecuteToolResult(BaseModel):
    """Result from execute_tool node execution (merged route_tool + call_tool)."""
    status: str = Field(description="Execution status: 'success' or 'error'")
    error: Optional[str] = Field(default=None, description="Error message if status is 'error'")
    error_type: Optional[str] = Field(default=None, description="Type of error if status is 'error'")
    
    tool_name: Optional[str] = Field(default=None, description="Name of executed tool")
    result: Optional[Dict[str, Any]] = Field(default=None, description="Tool execution result")
    result_type: Optional[str] = Field(default=None, description="Type of result returned")
    routing_decision: Optional[Dict[str, Any]] = Field(default=None, description="Routing decision details")
    execution_time: Optional[float] = Field(default=None, description="Execution time in seconds")


class EvaluateResult(BaseModel):
    """Result from evaluate node execution."""
    status: str = Field(description="Execution status: 'success' or 'error'")
    error: Optional[str] = Field(default=None, description="Error message if status is 'error'")
    error_type: Optional[str] = Field(default=None, description="Type of error if status is 'error'")
    
    retry_count: int = Field(description="Current retry count")
    max_retries: int = Field(description="Maximum retry count")
    evaluation_timestamp: str = Field(description="When evaluation occurred")
    decision_reason: str = Field(description="Reason for decision")
    goal_complete: Optional[bool] = Field(default=None, description="Whether goal is complete")
    next_action: Optional[str] = Field(default=None, description="Next action to take")


class DiagnoseResult(BaseModel):
    """Result from diagnose node execution."""
    status: str = Field(description="Execution status: 'success' or 'error'")
    error: Optional[str] = Field(default=None, description="Error message if status is 'error'")
    error_type: Optional[str] = Field(default=None, description="Type of error if status is 'error'")
    
    error_classification: str = Field(description="Classification of the error")
    remediation_strategy: str = Field(description="Strategy for remediation")
    confidence: float = Field(description="Confidence in diagnosis")
    recommended_action: str = Field(description="Recommended action to take")


class AnswerResult(BaseModel):
    """Result from answer node execution."""
    status: str = Field(description="Execution status: 'success' or 'error'")
    error: Optional[str] = Field(default=None, description="Error message if status is 'error'")
    error_type: Optional[str] = Field(default=None, description="Type of error if status is 'error'")
    
    summary: str = Field(description="Summary of execution")
    steps_taken: int = Field(description="Number of steps taken")
    artifacts_created: int = Field(description="Number of artifacts created")
    final_result: Dict[str, Any] = Field(description="Final execution result")


class EscalateResult(BaseModel):
    """Result from escalate node execution."""
    status: str = Field(description="Execution status: 'success' or 'error'")
    error: Optional[str] = Field(default=None, description="Error message if status is 'error'")
    error_type: Optional[str] = Field(default=None, description="Type of error if status is 'error'")


# Generic response wrapper using TypeVar
T = TypeVar('T', bound=BaseModel)


class GenericNodeResponse(BaseModel, Generic[T]):
    """Generic response wrapper for all node types, eliminating redundant response patterns.
    
    This implements the streamlined response architecture by providing a single
    wrapper that can hold any node-specific result type, as specified in Phase 6.
    """
    # Standard fields (replacing redundant response patterns)
    current_step: str = Field(description="Next step to execute")
    current_attempt: Optional[int] = Field(default=None, description="Current attempt number when relevant")
    progress: List[str] = Field(default_factory=list, description="Progress messages")
    artifacts: List[Artifact] = Field(default_factory=list, description="Artifacts created during execution")
    failures: List[Failure] = Field(default_factory=list, description="Failures that occurred")
    error_context: Optional[ErrorContext] = Field(default=None, description="Error context if applicable")
    
    # Node-specific result (the streamlined approach)
    result: T = Field(description="Node-specific result object")
    
    # Additional node-specific fields that may be needed
    tool_signature: Optional[Dict[str, Any]] = Field(default=None, description="Tool signature when relevant")
    todo_list: List[TodoItem] = Field(default_factory=list, description="Todo list when relevant")
    goal_spec: Optional[GoalSpec] = Field(default=None, description="Goal specification when relevant")


# Context for escalation (this is specific and kept separate)
class EscalateContext(BaseModel):
    """Context for escalation to human input."""
    reason: str = Field(description="Reason for escalation")
    error: str = Field(description="Error that triggered escalation")
    options: List[str] = Field(description="Available options for human")
    recommended_action: str = Field(description="Recommended action")


# Type aliases for specific node responses using the generic wrapper
ParseGoalResponse = GenericNodeResponse[ParseGoalResult]
PlanStepResponse = GenericNodeResponse[PlanStepResult]
ExecuteToolResponse = GenericNodeResponse[ExecuteToolResult]
EvaluateResponse = GenericNodeResponse[EvaluateResult]
DiagnoseResponse = GenericNodeResponse[DiagnoseResult]
AnswerResponse = GenericNodeResponse[AnswerResult]
EscalateResponse = GenericNodeResponse[EscalateResult]


# For backward compatibility - union of all possible responses
NodeResponse = Union[
    ParseGoalResponse,
    PlanStepResponse, 
    ExecuteToolResponse,
    EvaluateResponse,
    DiagnoseResponse,
    AnswerResponse,
    EscalateResponse
]