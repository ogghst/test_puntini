"""Data models and schemas for the Puntini Agent system.

This module contains all the core data models including base entities,
graph elements, specifications, and error classes. All models inherit
from BaseEntity which provides UUIDv4 id generation and timestamp management.
"""

from .base import BaseEntity
from .node import Node
from .edge import Edge
from .patch import Patch
from .specs import (
    NodeSpec,
    EdgeSpec,
    MatchSpec,
    ToolSpec,
    PatchSpec,
)
from .errors import (
    AgentError,
    ValidationError,
    ConstraintViolationError,
    NotFoundError,
    DuplicateError,
    ToolError,
    PlanningError,
    QueryError,
    EscalationError,
    TracerError,
)
from .entities import (
    Project,
    User,
    Issue,
    Priority,
    Status,
)
from .goal_schemas import (
    GoalSpec,
    EntitySpec,
    ConstraintSpec,
    DomainHint,
    GoalComplexity,
    GraphElementType,
)

__all__ = [
    # Base models
    "BaseEntity",
    "Node",
    "Edge", 
    "Patch",
    
    # Specifications
    "NodeSpec",
    "EdgeSpec",
    "MatchSpec",
    "ToolSpec",
    "PatchSpec",
    
    # Error classes
    "AgentError",
    "ValidationError",
    "ConstraintViolationError",
    "NotFoundError",
    "DuplicateError",
    "ToolError",
    "PlanningError",
    "QueryError",
    "EscalationError",
    "TracerError",
    
    # Domain entities
    "Project",
    "User",
    "Issue",
    "Priority",
    "Status",
    
    # Goal schemas
    "GoalSpec",
    "EntitySpec",
    "ConstraintSpec",
    "DomainHint",
    "GoalComplexity",
    "GraphElementType",
]
