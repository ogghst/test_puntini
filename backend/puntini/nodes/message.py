"""Message classes for node outputs with streamlined response architecture.

This module defines Pydantic models for structured outputs from nodes,
providing type safety and validation for all node responses. This implements
the streamlined response architecture from Phase 6 of the refactoring plan.

The streamlined architecture uses a generic response wrapper with node-specific
result types to eliminate redundant response patterns as specified in the plan.
"""

from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING, Generic, TypeVar
from pydantic import BaseModel, Field
from datetime import datetime

from ..models.goal_schemas import TodoItem, GoalSpec

if TYPE_CHECKING:
    from .plan_step import StepPlan, ToolSignature


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


# Base classes for common patterns

class BaseResult(BaseModel):
    """Base class for all result types with common fields."""
    status: str = Field(description="Execution status: 'success' or 'error'")
    error: Optional[str] = Field(default=None, description="Error message if status is 'error'")
    error_type: Optional[str] = Field(default=None, description="Type of error if status is 'error'")


class BaseResponse(BaseModel):
    """Base class for all response types with common fields."""
    current_step: str = Field(description="Next step to execute")
    progress: List[str] = Field(default_factory=list, description="Progress messages")
    artifacts: List[Artifact] = Field(default_factory=list, description="Artifacts created during execution")
    failures: List[Failure] = Field(default_factory=list, description="Failures that occurred")
    result: Optional[Any] = Field(default=None, description="Execution result")
    error_context: Optional[ErrorContext] = Field(default=None, description="Error context if applicable")


class ExecutionResult(BaseResult):
    """Base class for execution results with execution-specific fields."""
    execution_time: Optional[float] = Field(default=None, description="Execution time in seconds")


class PlanningResult(BaseResult):
    """Base class for planning results with planning-specific fields."""
    is_final_step: Optional[bool] = Field(default=None, description="Whether this is the final step")
    overall_progress: Optional[float] = Field(default=None, description="Overall progress towards goal")


class EvaluationResult(BaseResult):
    """Base class for evaluation results with evaluation-specific fields."""
    retry_count: int = Field(description="Current retry count")
    max_retries: int = Field(description="Maximum retry count")
    evaluation_timestamp: str = Field(description="When evaluation occurred")
    decision_reason: str = Field(description="Reason for decision")
    goal_complete: Optional[bool] = Field(default=None, description="Whether goal is complete")
    next_action: Optional[str] = Field(default=None, description="Next action to take")


class DiagnosisResult(BaseResult):
    """Base class for diagnosis results with diagnosis-specific fields."""
    error_classification: str = Field(description="Classification of the error")
    remediation_strategy: str = Field(description="Strategy for remediation")
    confidence: float = Field(description="Confidence in diagnosis")
    recommended_action: str = Field(description="Recommended action to take")


class AnswerResultBase(BaseResult):
    """Base class for answer results with answer-specific fields."""
    summary: str = Field(description="Summary of execution")
    steps_taken: int = Field(description="Number of steps taken")
    artifacts_created: int = Field(description="Number of artifacts created")
    final_result: Dict[str, Any] = Field(description="Final execution result")


class ParseGoalResult(BaseResult):
    """Result from parse_goal node execution."""
    parsed_goal: Optional[Dict[str, Any]] = Field(default=None, description="Parsed goal data")
    complexity: Optional[str] = Field(default=None, description="Goal complexity level")
    requires_graph_ops: Optional[bool] = Field(default=None, description="Whether goal requires graph operations")
    is_simple: Optional[bool] = Field(default=None, description="Whether goal is simple")
    retryable: Optional[bool] = Field(default=None, description="Whether error is retryable")


class ParseGoalResponse(BaseResponse):
    """Complete response from parse_goal node."""
    current_attempt: int = Field(description="Current attempt number")
    failures: List[Failure] = Field(default_factory=list, description="Failures that occurred")
    result: ParseGoalResult = Field(description="Execution result")
    goal_spec: Optional[GoalSpec] = Field(default=None, description="Parsed goal specification")
    todo_list: List[TodoItem] = Field(default_factory=list, description="List of todos for goal execution")


class PlanStepResult(PlanningResult):
    """Result from plan_step node execution."""
    step_plan: Optional["StepPlan"] = Field(default=None, description="Generated step plan")


class PlanStepResponse(BaseResponse):
    """Complete response from plan_step node."""
    tool_signature: Optional[Dict[str, Any]] = Field(default=None, description="Tool signature for execution")
    failures: List[Failure] = Field(default_factory=list, description="Failures that occurred")
    result: PlanStepResult = Field(description="Execution result")


class RouteToolResult(BaseResult):
    """Result from route_tool node execution."""
    routing_decision: Optional[Dict[str, Any]] = Field(default=None, description="Routing decision details")


class RouteToolResponse(BaseResponse):
    """Complete response from route_tool node."""
    tool_signature: Optional[Dict[str, Any]] = Field(default=None, description="Validated tool signature")


class CallToolResult(ExecutionResult):
    """Result from call_tool node execution."""
    tool_name: Optional[str] = Field(default=None, description="Name of executed tool")
    result: Optional[Dict[str, Any]] = Field(default=None, description="Tool execution result")
    result_type: Optional[str] = Field(default=None, description="Type of result returned")


class CallToolResponse(BaseResponse):
    """Complete response from call_tool node."""
    result: CallToolResult = Field(description="Tool execution result")


class ExecuteToolResult(ExecutionResult):
    """Result from execute_tool node execution (merged route_tool + call_tool)."""
    tool_name: Optional[str] = Field(default=None, description="Name of executed tool")
    result: Optional[Dict[str, Any]] = Field(default=None, description="Tool execution result")
    result_type: Optional[str] = Field(default=None, description="Type of result returned")
    routing_decision: Optional[Dict[str, Any]] = Field(default=None, description="Routing decision details")


class ExecuteToolResponse(BaseResponse):
    """Complete response from execute_tool node (merged route_tool + call_tool)."""
    result: ExecuteToolResult = Field(description="Tool execution result")
    tool_signature: Optional[Dict[str, Any]] = Field(default=None, description="Validated tool signature")


class EvaluateResult(EvaluationResult):
    """Result from evaluate node execution."""
    pass


class EvaluateResponse(BaseResponse):
    """Complete response from evaluate node."""
    result: EvaluateResult = Field(description="Evaluation result")
    todo_list: List[TodoItem] = Field(default_factory=list, description="Updated todo list")


class DiagnoseResult(DiagnosisResult):
    """Result from diagnose node execution."""
    pass


class DiagnoseResponse(BaseResponse):
    """Complete response from diagnose node."""
    pass


class EscalateContext(BaseModel):
    """Context for escalation to human input."""
    reason: str = Field(description="Reason for escalation")
    error: str = Field(description="Error that triggered escalation")
    options: List[str] = Field(description="Available options for human")
    recommended_action: str = Field(description="Recommended action")


class EscalateResponse(BaseResponse):
    """Complete response from escalate node."""
    escalation_context: Optional[EscalateContext] = Field(default=None, description="Escalation context")


class AnswerResult(AnswerResultBase):
    """Result from answer node execution."""
    pass


class AnswerResponse(BaseResponse):
    """Complete response from answer node."""
    result: AnswerResult = Field(description="Answer result")


# Union type for all possible node responses
NodeResponse = Union[
    ParseGoalResponse,
    PlanStepResponse,
    RouteToolResponse,
    CallToolResponse,
    EvaluateResponse,
    DiagnoseResponse,
    EscalateResponse,
    AnswerResponse
]


# Rebuild models to resolve forward references
def _rebuild_models():
    """Rebuild models to resolve forward references."""
    try:
        from .plan_step import StepPlan, ToolSignature
        PlanStepResult.model_rebuild()
    except ImportError:
        # Skip rebuild if plan_step module is not available
        pass

_rebuild_models()
