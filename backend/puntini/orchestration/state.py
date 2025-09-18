"""State schema and reducers for the agent.

This module defines the state schema and reducer functions for the
LangGraph state machine, ensuring proper state management and updates.
"""

from typing import Any, Dict, List, Optional, Union
from typing_extensions import Annotated
from operator import add

# Import the State schema from the separate file to avoid circular imports
from .state_schema import State


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

