"""Return type models for graph node functions with streamlined architecture.

This module defines Pydantic models for the return types of graph node functions,
implementing the streamlined response architecture from Phase 6 of the refactoring plan.
This eliminates redundant response patterns by using generic return types with 
node-specific result types as specified in the plan.
"""

from typing import Any, Dict, List, Optional, Union, Literal, Generic, TypeVar
from pydantic import BaseModel, Field
from datetime import datetime

# Import streamlined architecture components
from .streamlined_message import (
    Artifact, Failure, ErrorContext, EscalateContext,
    ParseGoalResult, PlanStepResult, ExecuteToolResult, EvaluateResult,
    DiagnoseResult, AnswerResult, EscalateResult
)

# Legacy imports for backward compatibility
from .message import (
    BaseResult, BaseResponse, ExecutionResult, PlanningResult,
    EvaluationResult as LegacyEvaluationResult, DiagnosisResult, AnswerResultBase
)


# Generic return type using TypeVar for node-specific results
T = TypeVar('T')

class GenericNodeReturn(BaseModel, Generic[T]):
    """Generic return type that can hold any node-specific result type."""
    
    model_config = {
        "arbitrary_types_allowed": True,
        "validate_assignment": True,
        "extra": "forbid"
    }
    
    # Common fields for all node returns
    current_step: str = Field(description="Next step to execute")
    progress: List[str] = Field(default_factory=list, description="Progress messages")
    artifacts: List[Artifact] = Field(default_factory=list, description="Artifacts created during execution")
    failures: List[Failure] = Field(default_factory=list, description="Failures that occurred")
    result: Optional[Dict[str, Any]] = Field(default=None, description="Execution result")
    
    # Node-specific result object
    node_result: Optional[T] = Field(default=None, description="Node-specific result object")
    
    # Additional fields that may be needed
    current_attempt: Optional[int] = Field(default=None, description="Current attempt number when relevant")
    tool_signature: Optional[Dict[str, Any]] = Field(default=None, description="Tool signature when relevant")
    todo_list: List = Field(default_factory=list, description="Todo list when relevant")
    goal_spec: Optional[Dict[str, Any]] = Field(default=None, description="Goal specification when relevant")
    escalation_context: Optional[EscalateContext] = Field(default=None, description="Escalation context when relevant")
    
    def to_state_update(self) -> Dict[str, Any]:
        """Convert to state update including node-specific result."""
        return {
            "current_step": self.current_step,
            "progress": self.progress,
            "artifacts": self.artifacts,
            "failures": self.failures,
            "result": self.result,
            "node_result": self.node_result,
            "current_attempt": self.current_attempt,
            "tool_signature": self.tool_signature,
            "todo_list": self.todo_list,
            "goal_spec": self.goal_spec,
            "escalation_context": self.escalation_context
        }


# Streamlined return types using generic pattern with node-specific result types
class RouteToolReturn(GenericNodeReturn[ParseGoalResult]):
    """Return type for route_tool node function using streamlined architecture.
    
    Implements the generic response wrapper with node-specific result types
    as specified in Phase 6 of the refactoring plan to eliminate redundant 
    response patterns. This is a legacy class that will be deprecated in favor
    of ExecuteToolReturn which merges route_tool + call_tool functionality.
    """
    pass


class CallToolReturn(GenericNodeReturn[ExecuteToolResult]):
    """Return type for call_tool node function using streamlined architecture.
    
    Implements the generic response wrapper with node-specific result types
    as specified in Phase 6 of the refactoring plan to eliminate redundant 
    response patterns. This is a legacy class that will be deprecated in favor
    of ExecuteToolReturn which merges route_tool + call_tool functionality.
    """
    pass


class ParseGoalReturn(GenericNodeReturn[ParseGoalResult]):
    """Return type for parse_goal node function using streamlined architecture.
    
    Implements the generic response wrapper with node-specific result types
    as specified in Phase 6 of the refactoring plan to eliminate redundant 
    response patterns.
    """
    pass


class PlanStepReturn(GenericNodeReturn[PlanStepResult]):
    """Return type for plan_step node function using streamlined architecture.
    
    Implements the generic response wrapper with node-specific result types
    as specified in Phase 6 of the refactoring plan to eliminate redundant 
    response patterns.
    """
    pass


class ExecuteToolReturn(GenericNodeReturn[ExecuteToolResult]):
    """Return type for execute_tool node function using streamlined architecture.
    
    Implements the generic response wrapper with node-specific result types
    as specified in Phase 6 of the refactoring plan to eliminate redundant 
    response patterns. Merges functionality of route_tool + call_tool.
    """
    pass


class EvaluateReturn(GenericNodeReturn[EvaluateResult]):
    """Return type for evaluate node function using streamlined architecture.
    
    Implements the generic response wrapper with node-specific result types
    as specified in Phase 6 of the refactoring plan to eliminate redundant 
    response patterns.
    """
    pass


class DiagnoseReturn(GenericNodeReturn[DiagnoseResult]):
    """Return type for diagnose node function using streamlined architecture.
    
    Implements the generic response wrapper with node-specific result types
    as specified in Phase 6 of the refactoring plan to eliminate redundant 
    response patterns.
    """
    pass


class AnswerReturn(GenericNodeReturn[AnswerResult]):
    """Return type for answer node function using streamlined architecture.
    
    Implements the generic response wrapper with node-specific result types
    as specified in Phase 6 of the refactoring plan to eliminate redundant 
    response patterns.
    """
    pass


class EscalateReturn(GenericNodeReturn[EscalateResult]):
    """Return type for escalate node function using streamlined architecture.
    
    Implements the generic response wrapper with node-specific result types
    as specified in Phase 6 of the refactoring plan to eliminate redundant 
    response patterns.
    """
    pass


# Command return types for functions that return Command objects (streamlined)
class CommandReturn(BaseModel):
    """Base class for Command return types (streamlined architecture)."""
    
    model_config = {
        "arbitrary_types_allowed": True,
        "validate_assignment": True,
        "extra": "forbid"
    }
    
    # Command-specific fields
    update: Optional[Dict[str, Any]] = Field(default=None, description="State updates")
    goto: Optional[str] = Field(default=None, description="Next node to execute")
    resume: Optional[str] = Field(default=None, description="Resume value for human-in-the-loop")


class EvaluateCommandReturn(CommandReturn):
    """Return type for evaluate node function that returns Command (streamlined)."""
    
    evaluate_response: Optional[Any] = Field(default=None, description="Evaluate response object")


class EscalateCommandReturn(CommandReturn):
    """Return type for escalate node function that returns Command (streamlined)."""
    
    escalate_response: Optional[Any] = Field(default=None, description="Escalate response object")
    escalation_context: Optional[EscalateContext] = Field(default=None, description="Escalation context")


# Union type for all possible node return types (streamlined)
NodeReturn = Union[
    ParseGoalReturn,
    PlanStepReturn,
    ExecuteToolReturn,
    DiagnoseReturn,
    AnswerReturn,
    EvaluateCommandReturn,
    EscalateCommandReturn
]


# Type aliases for specific return patterns (streamlined)
StateUpdate = Dict[str, Any]
CommandUpdate = Dict[str, Any]


# Type aliases for specific return patterns
StateUpdate = Dict[str, Any]
CommandUpdate = Dict[str, Any]
