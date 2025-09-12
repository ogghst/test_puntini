"""Error models for the agent system.

This module defines custom exception classes and error types
used throughout the agent system.
"""

from typing import Any, Dict, Optional


class AgentError(Exception):
    """Base exception for all agent-related errors."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        """Initialize the agent error.
        
        Args:
            message: Human-readable error message.
            error_code: Optional error code for programmatic handling.
            details: Optional additional error details.
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}


class ValidationError(AgentError):
    """Raised when input validation fails."""
    pass


class ConstraintViolationError(AgentError):
    """Raised when database constraints are violated."""
    pass


class NotFoundError(AgentError):
    """Raised when a requested resource is not found."""
    pass


class DuplicateError(AgentError):
    """Raised when attempting to create a duplicate resource."""
    pass


class ToolError(AgentError):
    """Raised when tool execution fails."""
    pass


class PlanningError(AgentError):
    """Raised when planning fails."""
    pass


class QueryError(AgentError):
    """Raised when a database query fails."""
    pass


class EscalationError(AgentError):
    """Raised when escalation handling fails."""
    pass


class TracerError(AgentError):
    """Raised when tracing operations fail."""
    pass

