"""Return type models for graph node functions.

This module defines Pydantic models for the return types of graph node functions,
providing type safety and validation for all node function returns.
"""

from typing import Any, Dict, List, Optional, Union, Literal
from pydantic import BaseModel, Field
from datetime import datetime

from .message import (
    Artifact, Failure, ErrorContext, EscalateContext,
    BaseResult, BaseResponse, ExecutionResult, PlanningResult,
    EvaluationResult, DiagnosisResult, AnswerResultBase
)


class NodeReturnBase(BaseModel):
    """Base class for all node return types with common fields."""
    
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
    
    def to_state_update(self) -> Dict[str, Any]:
        """Convert the return type to a state update dictionary for LangGraph.
        
        Returns:
            Dictionary representing state updates that can be applied by LangGraph.
        """
        return {
            "current_step": self.current_step,
            "progress": self.progress,
            "artifacts": self.artifacts,
            "failures": self.failures,
            "result": self.result
        }


class ParseGoalReturn(NodeReturnBase):
    """Return type for parse_goal node function."""
    
    current_attempt: int = Field(description="Current attempt number")
    parse_goal_response: Optional[Any] = Field(default=None, description="Parse goal response object")
    
    def to_state_update(self) -> Dict[str, Any]:
        """Convert to state update including parse_goal specific fields."""
        base_update = super().to_state_update()
        base_update.update({
            "current_attempt": self.current_attempt,
            "parse_goal_response": self.parse_goal_response
        })
        
        # Include todo_list and goal_spec from the response if available
        if self.parse_goal_response:
            if hasattr(self.parse_goal_response, 'todo_list'):
                base_update["todo_list"] = self.parse_goal_response.todo_list
            if hasattr(self.parse_goal_response, 'goal_spec'):
                base_update["goal_spec"] = self.parse_goal_response.goal_spec
        
        return base_update


class PlanStepReturn(NodeReturnBase):
    """Return type for plan_step node function."""
    
    plan_step_response: Optional[Any] = Field(default=None, description="Plan step response object")
    tool_signature: Optional[Dict[str, Any]] = Field(default=None, description="Tool signature for execution")
    
    def to_state_update(self) -> Dict[str, Any]:
        """Convert to state update including plan_step specific fields."""
        base_update = super().to_state_update()
        base_update.update({
            "plan_step_response": self.plan_step_response,
            "tool_signature": self.tool_signature
        })
        
        # Preserve todo_list from state (plan_step doesn't modify it)
        # Note: This will be handled by LangGraph state preservation
        
        return base_update


class RouteToolReturn(NodeReturnBase):
    """Return type for route_tool node function."""
    
    route_tool_response: Optional[Any] = Field(default=None, description="Route tool response object")
    tool_signature: Optional[Dict[str, Any]] = Field(default=None, description="Validated tool signature")
    
    def to_state_update(self) -> Dict[str, Any]:
        """Convert to state update including route_tool specific fields."""
        base_update = super().to_state_update()
        base_update.update({
            "route_tool_response": self.route_tool_response,
            "tool_signature": self.tool_signature
        })
        return base_update


class CallToolReturn(NodeReturnBase):
    """Return type for call_tool node function."""
    
    call_tool_response: Optional[Any] = Field(default=None, description="Call tool response object")
    
    def to_state_update(self) -> Dict[str, Any]:
        """Convert to state update including call_tool specific fields."""
        base_update = super().to_state_update()
        base_update.update({
            "call_tool_response": self.call_tool_response
        })
        return base_update


class DiagnoseReturn(NodeReturnBase):
    """Return type for diagnose node function."""
    
    diagnose_response: Optional[Any] = Field(default=None, description="Diagnose response object")
    error_context: Optional[ErrorContext] = Field(default=None, description="Error context for diagnosis")
    
    def to_state_update(self) -> Dict[str, Any]:
        """Convert to state update including diagnose specific fields."""
        base_update = super().to_state_update()
        base_update.update({
            "diagnose_response": self.diagnose_response,
            "error_context": self.error_context
        })
        return base_update


class AnswerReturn(NodeReturnBase):
    """Return type for answer node function."""
    
    answer_response: Optional[Any] = Field(default=None, description="Answer response object")
    
    def to_state_update(self) -> Dict[str, Any]:
        """Convert to state update including answer specific fields."""
        base_update = super().to_state_update()
        base_update.update({
            "answer_response": self.answer_response
        })
        return base_update


class EvaluateReturn(NodeReturnBase):
    """Return type for evaluate node function."""
    
    evaluate_response: Optional[Any] = Field(default=None, description="Evaluate response object")
    
    def to_state_update(self) -> Dict[str, Any]:
        """Convert to state update including evaluate specific fields."""
        base_update = super().to_state_update()
        base_update.update({
            "evaluate_response": self.evaluate_response
        })
        return base_update


# Command return types for functions that return Command objects
class CommandReturn(BaseModel):
    """Base class for Command return types."""
    
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
    """Return type for evaluate node function that returns Command."""
    
    evaluate_response: Optional[Any] = Field(default=None, description="Evaluate response object")


class EscalateCommandReturn(CommandReturn):
    """Return type for escalate node function that returns Command."""
    
    escalate_response: Optional[Any] = Field(default=None, description="Escalate response object")
    escalation_context: Optional[EscalateContext] = Field(default=None, description="Escalation context")


# Union type for all possible node return types
NodeReturn = Union[
    ParseGoalReturn,
    PlanStepReturn,
    RouteToolReturn,
    CallToolReturn,
    DiagnoseReturn,
    AnswerReturn,
    EvaluateCommandReturn,
    EscalateCommandReturn
]


# Type aliases for specific return patterns
StateUpdate = Dict[str, Any]
CommandUpdate = Dict[str, Any]
