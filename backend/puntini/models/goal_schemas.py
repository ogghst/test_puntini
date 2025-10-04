"""Pydantic schemas for goal parsing and structured output.

This module defines the Pydantic models used for parsing and structuring
goals from natural language input using LangChain's structured output capabilities.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class GoalComplexity(str, Enum):
    """Enumeration of goal complexity levels."""
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"


class GraphElementType(str, Enum):
    """Semantic types for graph elements.
    
    Replaces the simplistic EntityType enum with proper semantic types
    that serve a useful purpose for graph operations.
    """
    NODE_REFERENCE = "node_ref"      # Reference to existing/new node
    EDGE_REFERENCE = "edge_ref"      # Reference to relationship  
    LITERAL_VALUE = "literal"        # Actual value, not entity
    SCHEMA_REFERENCE = "schema_ref"  # Reference to node label/edge type


class EntitySpec(BaseModel):
    """Specification for an entity extracted from a goal.
    
    Represents a specific entity (node, edge, property, etc.) that the
    goal involves manipulating or querying.
    """
    name: str = Field(description="The name or identifier of the entity")
    type: GraphElementType = Field(description="The type of graph element (node_ref, edge_ref, literal, schema_ref)")
    label: Optional[str] = Field(default=None, description="The label or category of the entity")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Properties associated with the entity")
    confidence: float = Field(ge=0.0, le=1.0, default=1.0, description="Confidence score for entity extraction")


class ConstraintSpec(BaseModel):
    """Specification for a constraint extracted from a goal.
    
    Represents a constraint or requirement that must be satisfied
    when executing the goal.
    """
    type: str = Field(description="The type of constraint (e.g., 'uniqueness', 'relationship', 'property')")
    description: str = Field(description="Human-readable description of the constraint")
    applies_to: Optional[str] = Field(default=None, description="What the constraint applies to (entity name or type)")
    severity: str = Field(default="medium", description="Severity level: low, medium, high")


class DomainHint(BaseModel):
    """Specification for a domain hint extracted from a goal.
    
    Represents domain-specific information that can help guide
    the execution of the goal.
    """
    domain: str = Field(description="The domain or context (e.g., 'project_management', 'social_network')")
    hint: str = Field(description="The specific hint or insight")
    relevance: float = Field(ge=0.0, le=1.0, description="Relevance score for the domain hint")


class TodoStatus(str, Enum):
    """Enumeration of todo item statuses."""
    PLANNED = "planned"
    DONE = "done"


class TodoItem(BaseModel):
    """Specification for a todo item in the goal execution plan.
    
    Represents a specific action that needs to be taken to complete
    the goal, with tracking of its completion status.
    """
    description: str = Field(description="Human-readable description of the action to be taken")
    status: TodoStatus = Field(default=TodoStatus.PLANNED, description="Current status of the todo item")
    step_number: Optional[int] = Field(default=None, description="Order in which this todo should be executed")
    dependencies: List[str] = Field(default_factory=list, description="IDs or descriptions of other todos this depends on")
    tool_name: Optional[str] = Field(default=None, description="Tool that will be used to complete this todo")
    estimated_complexity: str = Field(default="medium", description="Estimated complexity: low, medium, high")


class GoalSpec(BaseModel):
    """Complete specification for a parsed goal.
    
    This is the main schema that structures all information extracted
    from a natural language goal, including entities, constraints,
    domain hints, and execution metadata.
    """
    original_goal: str = Field(description="The original goal text as provided by the user")
    intent: str = Field(description="The primary intent or purpose of the goal")
    complexity: GoalComplexity = Field(description="The assessed complexity of the goal")
    
    # Extracted components
    entities: List[EntitySpec] = Field(default_factory=list, description="Entities involved in the goal")
    constraints: List[ConstraintSpec] = Field(default_factory=list, description="Constraints that must be satisfied")
    domain_hints: List[DomainHint] = Field(default_factory=list, description="Domain-specific hints and context")
    todo_list: List[TodoItem] = Field(default_factory=list, description="List of actions to be taken to complete the goal")
    
    # Execution metadata
    estimated_steps: int = Field(ge=1, default=1, description="Estimated number of steps to complete the goal")
    requires_human_input: bool = Field(default=False, description="Whether the goal requires human input or confirmation")
    priority: str = Field(default="medium", description="Priority level: low, medium, high, urgent")
    
    # Validation and quality
    confidence: float = Field(ge=0.0, le=1.0, description="Overall confidence in the goal parsing")
    parsing_notes: List[str] = Field(default_factory=list, description="Notes about the parsing process")

    @field_validator('entities')
    @classmethod
    def validate_entities(cls, v: List[EntitySpec]) -> List[EntitySpec]:
        """Validate that entities are properly specified."""
        if not v:
            return v
        
        # Check for duplicate entity names
        names = [entity.name for entity in v]
        if len(names) != len(set(names)):
            raise ValueError("Duplicate entity names found")
        
        return v

    @field_validator('constraints')
    @classmethod
    def validate_constraints(cls, v: List[ConstraintSpec]) -> List[ConstraintSpec]:
        """Validate that constraints are properly specified."""
        if not v:
            return v
        
        # Check for reasonable constraint descriptions
        for constraint in v:
            if len(constraint.description.strip()) < 3:
                raise ValueError(f"Constraint description too short: {constraint.description}")
        
        return v

    def get_entity_by_name(self, name: str) -> Optional[EntitySpec]:
        """Get an entity by its name.
        
        Args:
            name: The name of the entity to find.
            
        Returns:
            The EntitySpec if found, None otherwise.
        """
        for entity in self.entities:
            if entity.name == name:
                return entity
        return None

    def get_entities_by_type(self, entity_type: GraphElementType) -> List[EntitySpec]:
        """Get all entities of a specific type.
        
        Args:
            entity_type: The type of entities to find.
            
        Returns:
            List of EntitySpec instances matching the type.
        """
        return [entity for entity in self.entities if entity.type == entity_type]

    def get_constraints_by_type(self, constraint_type: str) -> List[ConstraintSpec]:
        """Get all constraints of a specific type.
        
        Args:
            constraint_type: The type of constraints to find.
            
        Returns:
            List of ConstraintSpec instances matching the type.
        """
        return [constraint for constraint in self.constraints if constraint.type == constraint_type]

    def is_simple_goal(self) -> bool:
        """Check if this is a simple goal that can be executed in one step.
        
        Returns:
            True if the goal is simple, False otherwise.
        """
        return (
            self.complexity == GoalComplexity.SIMPLE and
            len(self.entities) <= 2 and
            len(self.constraints) <= 1 and
            self.estimated_steps <= 1
        )

    def requires_graph_operations(self) -> bool:
        """Check if this goal requires graph database operations.
        
        Returns:
            True if the goal involves graph operations, False otherwise.
        """
        return any(
            entity.type in [GraphElementType.NODE_REFERENCE, GraphElementType.EDGE_REFERENCE]
            for entity in self.entities
        )

    def get_todo_by_description(self, description: str) -> Optional[TodoItem]:
        """Get a todo item by its description.
        
        Args:
            description: The description of the todo to find.
            
        Returns:
            The TodoItem if found, None otherwise.
        """
        for todo in self.todo_list:
            if todo.description == description:
                return todo
        return None

    def mark_todo_done(self, description: str) -> bool:
        """Mark a todo item as done.
        
        Args:
            description: The description of the todo to mark as done.
            
        Returns:
            True if the todo was found and marked, False otherwise.
        """
        todo = self.get_todo_by_description(description)
        if todo:
            todo.status = TodoStatus.DONE
            return True
        return False

    def get_remaining_todos(self) -> List[TodoItem]:
        """Get all todos that are not yet done.
        
        Returns:
            List of TodoItem instances with status 'planned'.
        """
        return [todo for todo in self.todo_list if todo.status == TodoStatus.PLANNED]

    def get_completed_todos(self) -> List[TodoItem]:
        """Get all todos that are done.
        
        Returns:
            List of TodoItem instances with status 'done'.
        """
        return [todo for todo in self.todo_list if todo.status == TodoStatus.DONE]

    def is_goal_complete(self) -> bool:
        """Check if all todos are completed.
        
        Returns:
            True if all todos are done, False otherwise.
        """
        return len(self.get_remaining_todos()) == 0
