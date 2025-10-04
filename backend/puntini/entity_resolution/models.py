"""Entity resolution models for graph-aware entity recognition.

This module defines the core data models for the entity resolution system,
addressing the fundamental flaws in the current entity recognition approach:

1. EntityMention: Represents a mention of an entity in text
2. EntityCandidate: Represents a potential match in the graph
3. EntityResolution: Represents the resolution strategy and result
4. EntityConfidence: Provides meaningful confidence scores based on graph similarity
5. GraphElementType: Semantic types for graph elements (replaces simplistic EntityType)
"""

from typing import Any, Dict, List, Literal, Optional
from enum import Enum
from uuid import UUID, uuid4
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class GraphElementType(str, Enum):
    """Semantic types for graph elements.
    
    Replaces the simplistic EntityType enum with proper semantic types
    that serve a useful purpose for graph operations.
    """
    NODE_REFERENCE = "node_ref"      # Reference to existing/new node
    EDGE_REFERENCE = "edge_ref"      # Reference to relationship  
    LITERAL_VALUE = "literal"        # Actual value, not entity
    SCHEMA_REFERENCE = "schema_ref"  # Reference to node label/edge type


class ResolutionStrategy(str, Enum):
    """Strategy for resolving entity mentions."""
    CREATE_NEW = "create_new"        # Create a new entity
    USE_EXISTING = "use_existing"    # Use an existing entity
    ASK_USER = "ask_user"           # Ask user to disambiguate


class ResolutionStatus(str, Enum):
    """Status of entity resolution process."""
    PENDING = "pending"              # Resolution not yet attempted
    RESOLVED = "resolved"            # Successfully resolved
    AMBIGUOUS = "ambiguous"          # Multiple candidates, needs disambiguation
    FAILED = "failed"               # Resolution failed


class EntityConfidence(BaseModel):
    """Meaningful confidence scores based on graph similarity and context.
    
    Replaces the meaningless confidence scores in the current system with
    proper confidence calculation based on:
    - String similarity to existing entities
    - Property overlap with candidates  
    - Context from surrounding entities
    - User feedback history
    """
    name_match: float = Field(
        ge=0.0, le=1.0, 
        description="String similarity score to existing entities"
    )
    type_match: float = Field(
        ge=0.0, le=1.0,
        description="Type compatibility score"
    )
    property_match: float = Field(
        ge=0.0, le=1.0,
        description="Property overlap score with candidates"
    )
    context_match: float = Field(
        ge=0.0, le=1.0,
        description="Context similarity from surrounding entities"
    )
    overall: float = Field(
        ge=0.0, le=1.0,
        description="Weighted combination of all scores"
    )
    
    @field_validator('overall')
    @classmethod
    def validate_overall(cls, v: float, info) -> float:
        """Validate that overall score is reasonable given component scores."""
        if hasattr(info, 'data') and info.data:
            # Calculate expected overall based on component scores
            expected = (
                info.data.get('name_match', 0) * 0.4 +
                info.data.get('type_match', 0) * 0.3 +
                info.data.get('property_match', 0) * 0.2 +
                info.data.get('context_match', 0) * 0.1
            )
            # Allow some tolerance for rounding
            if abs(v - expected) > 0.1:
                raise ValueError(f"Overall score {v} doesn't match expected {expected}")
        return v
    
    def is_certain(self) -> bool:
        """Check if confidence is high enough for automatic resolution."""
        return self.overall > 0.95
    
    def requires_human(self) -> bool:
        """Check if confidence is in the ambiguous range requiring human input."""
        return 0.3 < self.overall < 0.7
    
    def is_too_low(self) -> bool:
        """Check if confidence is too low for any resolution."""
        return self.overall < 0.3


class EntityMention(BaseModel):
    """Represents a mention of an entity in text.
    
    This is the first step in the entity resolution pipeline:
    Raw Text → Entity Mentions → Entity Candidates → Entity Linking → Resolved Entities
    """
    id: UUID = Field(default_factory=uuid4, description="Unique identifier for this mention")
    surface_form: str = Field(description="The text that mentions the entity")
    canonical_id: Optional[str] = Field(default=None, description="Resolved canonical entity ID")
    element_type: GraphElementType = Field(description="Type of graph element being referenced")
    candidates: List["EntityCandidate"] = Field(default_factory=list, description="Potential matches in the graph")
    confidence: Optional[EntityConfidence] = Field(default=None, description="Confidence in the mention")
    context: Dict[str, Any] = Field(default_factory=dict, description="Context around this mention")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When this mention was created")
    
    @field_validator('surface_form')
    @classmethod
    def validate_surface_form(cls, v: str) -> str:
        """Validate that surface form is not empty."""
        if not v or not v.strip():
            raise ValueError("Surface form cannot be empty")
        return v.strip()


class EntityCandidate(BaseModel):
    """Represents a potential match for an entity mention in the graph.
    
    Contains the actual graph entity information and similarity scores.
    """
    id: str = Field(description="Unique identifier of the candidate entity")
    name: str = Field(description="Name of the candidate entity")
    label: Optional[str] = Field(default=None, description="Node label or edge type")
    similarity: float = Field(ge=0.0, le=1.0, description="Similarity score to the mention")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Properties of the candidate")
    context: Dict[str, Any] = Field(default_factory=dict, description="Graph context around this candidate")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate that name is not empty."""
        if not v or not v.strip():
            raise ValueError("Candidate name cannot be empty")
        return v.strip()


class EntityResolution(BaseModel):
    """Represents the resolution of an entity mention.
    
    Contains the strategy and result of entity resolution.
    """
    mention_id: UUID = Field(description="ID of the resolved mention")
    strategy: ResolutionStrategy = Field(description="Resolution strategy used")
    entity_id: Optional[str] = Field(default=None, description="Resolved entity ID (if any)")
    confidence: EntityConfidence = Field(description="Confidence in the resolution")
    reasoning: str = Field(description="Explanation of why this resolution was chosen")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When this resolution was created")
    
    @field_validator('entity_id')
    @classmethod
    def validate_entity_id(cls, v: Optional[str], info) -> Optional[str]:
        """Validate entity_id based on strategy."""
        if hasattr(info, 'data') and info.data:
            strategy = info.data.get('strategy')
            if strategy == ResolutionStrategy.USE_EXISTING and not v:
                raise ValueError("entity_id is required when strategy is USE_EXISTING")
            if strategy == ResolutionStrategy.CREATE_NEW and v:
                raise ValueError("entity_id should not be set when strategy is CREATE_NEW")
        return v


class AmbiguityResolution(BaseModel):
    """Represents the resolution of ambiguous entity references.
    
    This should be in the state schema but wasn't in the current system.
    """
    id: UUID = Field(default_factory=uuid4, description="Unique identifier for this ambiguity")
    ambiguous_entities: List[EntityMention] = Field(description="Entities that are ambiguous")
    disambiguation_question: str = Field(description="Question to ask the user for disambiguation")
    candidates_per_entity: Dict[str, List[EntityCandidate]] = Field(
        description="Candidates for each ambiguous entity"
    )
    resolution_status: ResolutionStatus = Field(default=ResolutionStatus.PENDING, description="Current resolution status")
    user_response: Optional[Dict[str, Any]] = Field(default=None, description="User's disambiguation response")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When this ambiguity was created")
    resolved_at: Optional[datetime] = Field(default=None, description="When this ambiguity was resolved")
    
    @field_validator('disambiguation_question')
    @classmethod
    def validate_question(cls, v: str) -> str:
        """Validate that disambiguation question is not empty."""
        if not v or not v.strip():
            raise ValueError("Disambiguation question cannot be empty")
        return v.strip()
    
    def is_resolved(self) -> bool:
        """Check if this ambiguity has been resolved."""
        return self.resolution_status == ResolutionStatus.RESOLVED
    
    def is_pending(self) -> bool:
        """Check if this ambiguity is still pending resolution."""
        return self.resolution_status == ResolutionStatus.PENDING


# Update forward references
EntityMention.model_rebuild()
EntityResolution.model_rebuild()
AmbiguityResolution.model_rebuild()
