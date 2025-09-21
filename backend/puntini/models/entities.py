"""Entity models for semantic validation.

This module defines domain entity classes that inherit from BaseEntity
and are designed for semantic validation of unstructured data before
conversion to graph nodes and relationships.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from .base import BaseEntity


class Priority(str, Enum):
    """Priority levels for issues and tasks."""
    
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Status(str, Enum):
    """Status values for projects and issues."""
    
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"


class Project(BaseEntity):
    """Project entity for semantic validation.
    
    Represents a project in the system. This entity is used for semantic
    validation of unstructured project data before conversion to graph nodes.
    No relationships are defined here - they are handled at the graph level.
    
    Attributes:
        name: Project name (required, non-empty)
        description: Optional project description
        status: Current project status
        start_date: Optional project start date
        end_date: Optional project end date
        budget: Optional project budget (must be positive if provided)
        tags: Optional list of project tags
        metadata: Additional project metadata
    """
    
    name: str = Field(..., min_length=1, max_length=255, description="Project name")
    description: Optional[str] = Field(None, max_length=1000, description="Project description")
    status: Status = Field(default=Status.PLANNING, description="Project status")
    start_date: Optional[datetime] = Field(None, description="Project start date")
    end_date: Optional[datetime] = Field(None, description="Project end date")
    budget: Optional[float] = Field(None, gt=0, description="Project budget")
    tags: list[str] = Field(default_factory=list, description="Project tags")
    metadata: dict[str, str] = Field(default_factory=dict, description="Additional metadata")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate project name.
        
        Args:
            v: Project name to validate
            
        Returns:
            Validated project name
            
        Raises:
            ValueError: If name is empty or contains only whitespace
        """
        if not v.strip():
            raise ValueError("Project name cannot be empty or contain only whitespace")
        return v.strip()
    
    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        """Validate and normalize project tags.
        
        Args:
            v: List of tags to validate
            
        Returns:
            Normalized list of tags (trimmed, non-empty)
            
        Raises:
            ValueError: If any tag is empty or contains only whitespace
        """
        if not v:
            return []
        
        normalized_tags = []
        for tag in v:
            if not tag or not tag.strip():
                raise ValueError("Project tags cannot be empty or contain only whitespace")
            normalized_tags.append(tag.strip().lower())
        
        # Remove duplicates while preserving order
        seen = set()
        unique_tags = []
        for tag in normalized_tags:
            if tag not in seen:
                seen.add(tag)
                unique_tags.append(tag)
        
        return unique_tags
    
    @model_validator(mode='after')
    def validate_dates(self) -> 'Project':
        """Validate date relationships.
        
        Returns:
            Self after validation
            
        Raises:
            ValueError: If end_date is before start_date
        """
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("Project end date cannot be before start date")
        return self
    
    @model_validator(mode='after')
    def validate_status_dates(self) -> 'Project':
        """Validate status consistency with dates.
        
        Returns:
            Self after validation
            
        Raises:
            ValueError: If status is completed but no end_date is set
        """
        if self.status == Status.COMPLETED and not self.end_date:
            raise ValueError("Completed projects must have an end date")
        return self


class User(BaseEntity):
    """User entity for semantic validation.
    
    Represents a user in the system. This entity is used for semantic
    validation of unstructured user data before conversion to graph nodes.
    No relationships are defined here - they are handled at the graph level.
    
    Attributes:
        username: Unique username (required, non-empty)
        email: User email address (required, must be valid format)
        full_name: User's full name
        role: User role in the system
        is_active: Whether the user account is active
        last_login: Last login timestamp
        preferences: User preferences and settings
        metadata: Additional user metadata
    """
    
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    email: str = Field(..., description="User email address")
    full_name: Optional[str] = Field(None, max_length=255, description="User's full name")
    role: str = Field(default="user", max_length=50, description="User role")
    is_active: bool = Field(default=True, description="Whether user account is active")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    preferences: dict[str, str] = Field(default_factory=dict, description="User preferences")
    metadata: dict[str, str] = Field(default_factory=dict, description="Additional metadata")
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username format.
        
        Args:
            v: Username to validate
            
        Returns:
            Validated username (lowercase)
            
        Raises:
            ValueError: If username format is invalid
        """
        if not v.strip():
            raise ValueError("Username cannot be empty or contain only whitespace")
        
        username = v.strip().lower()
        
        # Check for valid characters (alphanumeric, underscore, hyphen)
        if not username.replace('_', '').replace('-', '').isalnum():
            raise ValueError("Username can only contain letters, numbers, underscores, and hyphens")
        
        # Check it doesn't start or end with special characters
        if username.startswith(('_', '-')) or username.endswith(('_', '-')):
            raise ValueError("Username cannot start or end with underscore or hyphen")
        
        return username
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format.
        
        Args:
            v: Email to validate
            
        Returns:
            Validated email (lowercase)
            
        Raises:
            ValueError: If email format is invalid
        """
        if not v.strip():
            raise ValueError("Email cannot be empty or contain only whitespace")
        
        email = v.strip().lower()
        
        # Basic email validation
        if '@' not in email or '.' not in email.split('@')[-1]:
            raise ValueError("Invalid email format")
        
        # Check for valid characters
        local, domain = email.split('@', 1)
        if not local or not domain:
            raise ValueError("Invalid email format")
        
        return email
    
    @field_validator('full_name')
    @classmethod
    def validate_full_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate and normalize full name.
        
        Args:
            v: Full name to validate
            
        Returns:
            Normalized full name or None
            
        Raises:
            ValueError: If full name format is invalid
        """
        if v is None:
            return None
        
        if not v.strip():
            raise ValueError("Full name cannot be empty or contain only whitespace")
        
        # Normalize whitespace and title case
        normalized = ' '.join(v.strip().split())
        return normalized.title()


class Issue(BaseEntity):
    """Issue entity for semantic validation.
    
    Represents an issue, bug, or task in the system. This entity is used for
    semantic validation of unstructured issue data before conversion to graph nodes.
    No relationships are defined here - they are handled at the graph level.
    
    Attributes:
        title: Issue title (required, non-empty)
        description: Optional issue description
        status: Current issue status
        priority: Issue priority level
        assignee: Optional username of assignee
        reporter: Username of issue reporter
        created_date: Issue creation date
        due_date: Optional issue due date
        estimated_hours: Optional estimated hours to complete
        actual_hours: Optional actual hours spent
        labels: Optional list of issue labels
        metadata: Additional issue metadata
    """
    
    title: str = Field(..., min_length=1, max_length=255, description="Issue title")
    description: Optional[str] = Field(None, max_length=2000, description="Issue description")
    status: Status = Field(default=Status.PLANNING, description="Issue status")
    priority: Priority = Field(default=Priority.MEDIUM, description="Issue priority")
    assignee: Optional[str] = Field(None, max_length=50, description="Username of assignee")
    reporter: str = Field(..., max_length=50, description="Username of reporter")
    created_date: datetime = Field(default_factory=datetime.utcnow, description="Creation date")
    due_date: Optional[datetime] = Field(None, description="Issue due date")
    estimated_hours: Optional[float] = Field(None, ge=0, description="Estimated hours to complete")
    actual_hours: Optional[float] = Field(None, ge=0, description="Actual hours spent")
    labels: list[str] = Field(default_factory=list, description="Issue labels")
    metadata: dict[str, str] = Field(default_factory=dict, description="Additional metadata")
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Validate issue title.
        
        Args:
            v: Issue title to validate
            
        Returns:
            Validated issue title
            
        Raises:
            ValueError: If title is empty or contains only whitespace
        """
        if not v.strip():
            raise ValueError("Issue title cannot be empty or contain only whitespace")
        return v.strip()
    
    @field_validator('assignee', 'reporter')
    @classmethod
    def validate_username_fields(cls, v: Optional[str]) -> Optional[str]:
        """Validate username fields (assignee, reporter).
        
        Args:
            v: Username to validate
            
        Returns:
            Validated username (lowercase) or None
            
        Raises:
            ValueError: If username format is invalid
        """
        if v is None:
            return None
        
        if not v.strip():
            raise ValueError("Username cannot be empty or contain only whitespace")
        
        username = v.strip().lower()
        
        # Check for valid characters (alphanumeric, underscore, hyphen)
        if not username.replace('_', '').replace('-', '').isalnum():
            raise ValueError("Username can only contain letters, numbers, underscores, and hyphens")
        
        return username
    
    @field_validator('labels')
    @classmethod
    def validate_labels(cls, v: list[str]) -> list[str]:
        """Validate and normalize issue labels.
        
        Args:
            v: List of labels to validate
            
        Returns:
            Normalized list of labels (trimmed, non-empty)
            
        Raises:
            ValueError: If any label is empty or contains only whitespace
        """
        if not v:
            return []
        
        normalized_labels = []
        for label in v:
            if not label or not label.strip():
                raise ValueError("Issue labels cannot be empty or contain only whitespace")
            normalized_labels.append(label.strip().lower())
        
        # Remove duplicates while preserving order
        seen = set()
        unique_labels = []
        for label in normalized_labels:
            if label not in seen:
                seen.add(label)
                unique_labels.append(label)
        
        return unique_labels
    
    @model_validator(mode='after')
    def validate_dates(self) -> 'Issue':
        """Validate date relationships.
        
        Returns:
            Self after validation
            
        Raises:
            ValueError: If due_date is before created_date
        """
        if self.due_date and self.due_date < self.created_date:
            raise ValueError("Issue due date cannot be before creation date")
        return self
    
    @model_validator(mode='after')
    def validate_hours(self) -> 'Issue':
        """Validate hours fields.
        
        Returns:
            Self after validation
            
        Raises:
            ValueError: If actual_hours is greater than estimated_hours by more than 50%
        """
        if (self.estimated_hours and self.actual_hours and 
            self.actual_hours > self.estimated_hours * 1.5):
            raise ValueError("Actual hours cannot exceed estimated hours by more than 50%")
        return self
    
    @model_validator(mode='after')
    def validate_status_hours(self) -> 'Issue':
        """Validate status consistency with hours.
        
        Returns:
            Self after validation
            
        Raises:
            ValueError: If status is completed but no actual_hours is set
        """
        if self.status == Status.COMPLETED and not self.actual_hours:
            raise ValueError("Completed issues should have actual hours recorded")
        return self
