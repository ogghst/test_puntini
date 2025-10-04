"""Intent parsing schemas for two-phase parsing architecture.

This module defines the Pydantic models for the first phase of parsing:
extracting minimal intent without graph context, as specified in Phase 2
of the progressive refactoring plan.
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from enum import Enum

from .goal_schemas import GoalComplexity


class IntentType(str, Enum):
    """Types of intents that can be extracted from user input."""
    CREATE = "create"
    QUERY = "query"
    UPDATE = "update"
    DELETE = "delete"
    UNKNOWN = "unknown"


class IntentSpec(BaseModel):
    """Specification for parsed intent (Phase 1 of two-phase parsing).
    
    This represents the minimal intent extracted without graph context,
    as specified in the progressive refactoring plan. This addresses
    the critical problem of premature full goal parsing identified in
    the graph critics analysis.
    """
    intent_type: IntentType = Field(description="The primary intent type")
    mentioned_entities: List[str] = Field(default_factory=list, description="Just strings, not resolved entities")
    requires_graph_context: bool = Field(description="Whether graph context is needed for entity resolution")
    complexity: GoalComplexity = Field(description="Assessed complexity for routing decisions")
    original_goal: str = Field(description="The original goal text")
    
    def is_simple_intent(self) -> bool:
        """Check if this is a simple intent that can be handled directly.
        
        Returns:
            True if the intent is simple and doesn't require graph context.
        """
        return (
            self.complexity == GoalComplexity.SIMPLE and
            not self.requires_graph_context and
            len(self.mentioned_entities) <= 2
        )


class ResolvedEntity(BaseModel):
    """A resolved entity with graph context (Phase 2 of two-phase parsing).
    
    This represents an entity that has been resolved with graph context,
    including similarity scores and disambiguation information.
    """
    mention: str = Field(description="Original mention text")
    entity_id: Optional[str] = Field(default=None, description="Resolved entity ID from graph")
    name: str = Field(description="Canonical name of the entity")
    entity_type: str = Field(description="Type of entity (User, Project, etc.)")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in the resolution")
    is_new: bool = Field(description="Whether this is a new entity to be created")
    properties: dict = Field(default_factory=dict, description="Entity properties")
    
    def is_ambiguous(self) -> bool:
        """Check if this entity resolution is ambiguous.
        
        Returns:
            True if the confidence is low and requires user disambiguation.
        """
        return 0.3 < self.confidence < 0.7


class Ambiguity(BaseModel):
    """Represents an ambiguous entity reference that requires user input.
    
    This addresses the critical problem of no handling of ambiguous references
    identified in the graph critics analysis.
    """
    mention: str = Field(description="The ambiguous mention text")
    candidates: List[dict] = Field(description="List of candidate entities with scores")
    disambiguation_question: str = Field(description="Question to ask the user")
    context: str = Field(description="Context to help with disambiguation")


class ResolvedGoalSpec(BaseModel):
    """Complete resolved goal specification (Phase 2 of two-phase parsing).
    
    This represents the goal after entity resolution with graph context,
    including resolved entities and any ambiguities that need user input.
    """
    intent_spec: IntentSpec = Field(description="The original intent specification")
    entities: List[ResolvedEntity] = Field(default_factory=list, description="Resolved entities with graph context")
    ambiguities: List[Ambiguity] = Field(default_factory=list, description="Ambiguous references requiring user input")
    ready_to_execute: bool = Field(description="Whether the goal is ready for execution")
    
    def has_ambiguities(self) -> bool:
        """Check if there are any ambiguities that need user input.
        
        Returns:
            True if there are ambiguities requiring user disambiguation.
        """
        return len(self.ambiguities) > 0
    
    def get_ambiguous_entities(self) -> List[ResolvedEntity]:
        """Get all entities that are ambiguous.
        
        Returns:
            List of entities with low confidence scores.
        """
        return [entity for entity in self.entities if entity.is_ambiguous()]
    
    def get_high_confidence_entities(self) -> List[ResolvedEntity]:
        """Get all entities with high confidence scores.
        
        Returns:
            List of entities with confidence >= 0.7.
        """
        return [entity for entity in self.entities if entity.confidence >= 0.7]
