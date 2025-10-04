"""Return type models for graph node functions using streamlined architecture.

This module defines Pydantic models for the return types of graph node functions,
implementing the streamlined response architecture by using generic return types
with node-specific result types, as specified in Phase 6 of the refactoring plan.
"""

from typing import Any, Dict, List, Optional, Union, Generic, TypeVar
from pydantic import BaseModel, Field
from datetime import datetime

from .streamlined_message import (
    Artifact, Failure, ErrorContext, EscalateContext,
    ParseGoalResult, PlanStepResult, ExecuteToolResult, EvaluateResult,
    DiagnoseResult, AnswerResult, EscalateResult
)


# Base class for streamlined return types
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


# Generic return type using TypeVar for node-specific results
T = TypeVar('T')

class GenericNodeReturn(NodeReturnBase, Generic[T]):
    """Generic return type that can hold any node-specific result type."""
    
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
        base_update = super().to_state_update()
        base_update.update({
            "node_result": self.node_result,
            "current_attempt": self.current_attempt,
            "tool_signature": self.tool_signature,
            "todo_list": self.todo_list,
            "goal_spec": self.goal_spec,
            "escalation_context": self.escalation_context
        })
        return base_update


# Specific return types using the generic pattern
class ParseGoalReturn(GenericNodeReturn[ParseGoalResult]):
    """Return type for parse_goal node function using streamlined architecture."""
    pass


class PlanStepReturn(GenericNodeReturn[PlanStepResult]):
    """Return type for plan_step node function using streamlined architecture."""
    pass


class ExecuteToolReturn(GenericNodeReturn[ExecuteToolResult]):
    """Return type for execute_tool node function using streamlined architecture."""
    pass


class EvaluateReturn(GenericNodeReturn[EvaluateResult]):
    """Return type for evaluate node function using streamlined architecture."""
    pass


class DiagnoseReturn(GenericNodeReturn[DiagnoseResult]):
    """Return type for diagnose node function using streamlined architecture."""
    pass


class AnswerReturn(GenericNodeReturn[AnswerResult]):
    """Return type for answer node function using streamlined architecture."""
    pass


class EscalateReturn(GenericNodeReturn[EscalateResult]):
    """Return type for escalate node function using streamlined architecture."""
    pass


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
    pass


class EscalateCommandReturn(CommandReturn):
    """Return type for escalate node function that returns Command."""
    pass


# Union type for all possible node return types
NodeReturn = Union[
    ParseGoalReturn,
    PlanStepReturn,
    ExecuteToolReturn,
    DiagnoseReturn,
    AnswerReturn,
    EvaluateCommandReturn,
    EscalateCommandReturn
]


# Type aliases for specific return patterns
StateUpdate = Dict[str, Any]
CommandUpdate = Dict[str, Any]