"""State schema and reducers for the agent.

This module defines the state schema and reducer functions for the
LangGraph state machine, ensuring proper state management and updates.
"""

from typing import Any, Dict, List
from typing_extensions import Annotated, TypedDict
from operator import add


class State(TypedDict):
    """State schema for the agent.
    
    The state contains all necessary information for the agent's execution
    including the goal, plan, progress, failures, and messages.
    """
    
    # Core goal and planning
    goal: str
    plan: List[str]
    progress: List[str]
    
    # Error handling and retry management
    failures: Annotated[List[Dict[str, Any]], add]
    retry_count: int
    max_retries: int
    
    # Communication and context
    messages: Annotated[List[Any], add]
    current_step: str
    current_attempt: int
    
    # Results and artifacts
    artifacts: Annotated[List[Dict[str, Any]], add]
    result: Dict[str, Any]
    
    # Private channels for inter-node data
    _tool_signature: Dict[str, Any]
    _error_context: Dict[str, Any]
    _escalation_context: Dict[str, Any]


def add_to_list(existing: List[Any] | None, updates: List[Any] | None) -> List[Any]:
    """Reducer function for adding items to a list.
    
    Args:
        existing: Existing list (None if not present).
        updates: New items to add (None if no updates).
        
    Returns:
        Updated list with new items appended.
    """
    if existing is None:
        existing = []
    if updates is None:
        return existing
    return existing + updates


def update_dict(existing: Dict[str, Any] | None, updates: Dict[str, Any] | None) -> Dict[str, Any]:
    """Reducer function for updating a dictionary.
    
    Args:
        existing: Existing dictionary (None if not present).
        updates: Updates to apply (None if no updates).
        
    Returns:
        Updated dictionary with new values.
    """
    if existing is None:
        existing = {}
    if updates is None:
        return existing
    return {**existing, **updates}


def increment_counter(existing: int | None, increment: int | None) -> int:
    """Reducer function for incrementing a counter.
    
    Args:
        existing: Existing counter value (None if not present).
        increment: Amount to increment (None if no increment).
        
    Returns:
        Updated counter value.
    """
    if existing is None:
        existing = 0
    if increment is None:
        return existing
    return existing + increment


def set_value(existing: Any | None, new_value: Any | None) -> Any:
    """Reducer function for setting a value.
    
    Args:
        existing: Existing value (ignored).
        new_value: New value to set.
        
    Returns:
        The new value.
    """
    return new_value

