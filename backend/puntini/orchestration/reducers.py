"""Reducer functions for state updates.

This module defines reducer functions that handle state updates
in a functional and predictable manner.
"""

from typing import Any, Dict, List, Optional
from operator import add


def add_to_list(existing: Optional[List[Any]], updates: Optional[List[Any]]) -> List[Any]:
    """Add items to a list, handling None values gracefully.
    
    Args:
        existing: Existing list (None if not present).
        updates: New items to add (None if no updates).
        
    Returns:
        Updated list with new items appended.
        
    Notes:
        This reducer ensures that list updates are additive and
        handle None values appropriately.
    """
    if existing is None:
        existing = []
    if updates is None:
        return existing
    return existing + updates


def update_dict(existing: Optional[Dict[str, Any]], updates: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Update a dictionary with new values.
    
    Args:
        existing: Existing dictionary (None if not present).
        updates: Updates to apply (None if no updates).
        
    Returns:
        Updated dictionary with new values merged in.
        
    Notes:
        This reducer performs a shallow merge of dictionaries,
        with updates taking precedence over existing values.
    """
    if existing is None:
        existing = {}
    if updates is None:
        return existing
    return {**existing, **updates}


def increment_counter(existing: Optional[int], increment: Optional[int]) -> int:
    """Increment a counter value.
    
    Args:
        existing: Existing counter value (None if not present).
        increment: Amount to increment (None if no increment).
        
    Returns:
        Updated counter value.
        
    Notes:
        This reducer handles None values by treating them as 0.
    """
    if existing is None:
        existing = 0
    if increment is None:
        return existing
    return existing + increment


def set_value(existing: Any, new_value: Any) -> Any:
    """Set a value, replacing any existing value.
    
    Args:
        existing: Existing value (ignored).
        new_value: New value to set.
        
    Returns:
        The new value.
        
    Notes:
        This reducer always returns the new value, effectively
        replacing any existing value.
    """
    return new_value


def append_to_string(existing: Optional[str], addition: Optional[str]) -> str:
    """Append to a string value.
    
    Args:
        existing: Existing string (None if not present).
        addition: String to append (None if no addition).
        
    Returns:
        Updated string with addition appended.
        
    Notes:
        This reducer handles None values by treating them as empty strings.
    """
    if existing is None:
        existing = ""
    if addition is None:
        return existing
    return existing + addition

