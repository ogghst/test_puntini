"""LangGraph node implementations for the agent workflow.

This module contains all the node functions that make up the agent's
state machine workflow. Each node handles a specific aspect of the
agent's execution including goal parsing, planning, tool execution,
evaluation, and error handling.
"""

from .parse_goal import parse_goal
from .plan_step import plan_step, ToolSignature, StepPlan
from .route_tool import route_tool
from .call_tool import call_tool
from .evaluate import evaluate
from .diagnose import diagnose
from .escalate import escalate
from .answer import answer
from .message import (
    # Base classes
    BaseResult, BaseResponse, ExecutionResult, PlanningResult, 
    EvaluationResult, DiagnosisResult, AnswerResultBase,
    # Concrete result classes
    ParseGoalResult, PlanStepResult, RouteToolResult, CallToolResult,
    EvaluateResult, DiagnoseResult, AnswerResult,
    # Concrete response classes
    ParseGoalResponse, PlanStepResponse, RouteToolResponse, CallToolResponse,
    EvaluateResponse, DiagnoseResponse, EscalateResponse, AnswerResponse,
    # Supporting classes
    Artifact, Failure, ErrorContext, EscalateContext, NodeResponse
)

# Import streamlined response architecture (Phase 6)
from .streamlined_message import (
    # Streamlined response classes
    GenericNodeResponse,
    ParseGoalResponse as StreamlinedParseGoalResponse,
    PlanStepResponse as StreamlinedPlanStepResponse,
    ExecuteToolResponse as StreamlinedExecuteToolResponse,
    EvaluateResponse as StreamlinedEvaluateResponse,
    DiagnoseResponse as StreamlinedDiagnoseResponse,
    AnswerResponse as StreamlinedAnswerResponse,
    EscalateResponse as StreamlinedEscalateResponse,
    # Streamlined result classes
    ParseGoalResult as StreamlinedParseGoalResult,
    PlanStepResult as StreamlinedPlanStepResult,
    ExecuteToolResult as StreamlinedExecuteToolResult,
    EvaluateResult as StreamlinedEvaluateResult,
    DiagnoseResult as StreamlinedDiagnoseResult,
    AnswerResult as StreamlinedAnswerResult,
    EscalateResult as StreamlinedEscalateResult,
    # Supporting classes
    EscalateContext as StreamlinedEscalateContext,
    Artifact as StreamlinedArtifact,
    Failure as StreamlinedFailure,
    ErrorContext as StreamlinedErrorContext
)

__all__ = [
    # Node functions
    "parse_goal",
    "plan_step",
    "route_tool", 
    "call_tool",
    "evaluate",
    "diagnose",
    "escalate",
    "answer",
    
    # Supporting schemas
    "ToolSignature",
    "StepPlan",
    
    # Base classes
    "BaseResult",
    "BaseResponse", 
    "ExecutionResult",
    "PlanningResult",
    "EvaluationResult",
    "DiagnosisResult",
    "AnswerResultBase",
    # Concrete result classes
    "ParseGoalResult",
    "PlanStepResult",
    "RouteToolResult",
    "CallToolResult",
    "EvaluateResult",
    "DiagnoseResult",
    "AnswerResult",
    # Concrete response classes
    "ParseGoalResponse",
    "PlanStepResponse", 
    "RouteToolResponse",
    "CallToolResponse",
    "EvaluateResponse",
    "DiagnoseResponse",
    "EscalateResponse",
    "AnswerResponse",
    # Supporting classes
    "Artifact",
    "Failure",
    "ErrorContext",
    "EscalateContext",
    "NodeResponse",
    
    # Streamlined response architecture (Phase 6)
    "GenericNodeResponse",
    "StreamlinedParseGoalResponse",
    "StreamlinedPlanStepResponse", 
    "StreamlinedExecuteToolResponse",
    "StreamlinedEvaluateResponse",
    "StreamlinedDiagnoseResponse",
    "StreamlinedAnswerResponse",
    "StreamlinedEscalateResponse",
    "StreamlinedParseGoalResult",
    "StreamlinedPlanStepResult",
    "StreamlinedExecuteToolResult",
    "StreamlinedEvaluateResult",
    "StreamlinedDiagnoseResult",
    "StreamlinedAnswerResult",
    "StreamlinedEscalateResult",
    "StreamlinedEscalateContext",
    "StreamlinedArtifact",
    "StreamlinedFailure",
    "StreamlinedErrorContext"
]
