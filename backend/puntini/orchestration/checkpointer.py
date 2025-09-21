"""Checkpointer configuration for state persistence.

This module provides checkpointer configuration and utilities
for persistent state management in the agent.
"""

from typing import Any, Dict, Optional
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.base import BaseCheckpointSaver


def create_checkpointer(checkpointer_type: str = "memory", **kwargs: Any) -> BaseCheckpointSaver:
    """Create a checkpointer instance based on the specified type.
    
    Args:
        checkpointer_type: Type of checkpointer to create ("memory", "neo4j", etc.).
        **kwargs: Additional configuration parameters.
        
    Returns:
        Configured checkpointer instance.
        
    Raises:
        ValueError: If the checkpointer type is not supported.
        
    Notes:
        Currently only supports "memory" type. Additional types like
        "neo4j" can be added as needed.
    """
    if checkpointer_type == "memory":
        return InMemorySaver()
    elif checkpointer_type == "neo4j":
        # TODO: Implement Neo4j checkpointer
        raise NotImplementedError("Neo4j checkpointer not yet implemented")
    else:
        raise ValueError(f"Unsupported checkpointer type: {checkpointer_type}")


def get_checkpoint_config(thread_id: str) -> Dict[str, Any]:
    """Get configuration for checkpoint operations.
    
    Args:
        thread_id: Unique thread identifier for state persistence.
        
    Returns:
        Configuration dictionary for checkpoint operations.
        
    Notes:
        The thread_id is used to isolate state between different
        agent execution sessions.
    """
    return {
        "configurable": {
            "thread_id": thread_id
        }
    }

