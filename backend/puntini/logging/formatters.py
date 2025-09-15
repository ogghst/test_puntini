"""Logging formatters for different output scenarios.

This module provides formatters for structured logging in different
environments (development, production, testing).
"""

import sys
from typing import Dict, Any, Callable
from loguru import logger


def create_formatters() -> Dict[str, str]:
    """Create formatters for different logging scenarios.
    
    Returns:
        Dictionary mapping formatter names to format strings.
    """
    return {
        "development": (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        ),
        "production": (
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
            "{level: <8} | "
            "{name}:{function}:{line} | "
            "{message}"
        ),
        "json": (
            '{{"timestamp": "{time:YYYY-MM-DD HH:mm:ss.SSS}", '
            '"level": "{level}", '
            '"module": "{name}", '
            '"function": "{function}", '
            '"line": {line}, '
            '"message": "{message}"}}'
        ),
        "minimal": "{time:HH:mm:ss} | {level} | {message}",
        "detailed": (
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
            "{level: <8} | "
            "{process.id} | "
            "{thread.id} | "
            "{name}:{function}:{line} | "
            "{message}"
        ),
    }


def create_console_formatter(use_colors: bool = True) -> str:
    """Create a console formatter with optional colors.
    
    Args:
        use_colors: Whether to include ANSI color codes.
        
    Returns:
        Format string for console output.
    """
    if use_colors and sys.stderr.isatty():
        return (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )
    else:
        return (
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
            "{level: <8} | "
            "{name}:{function}:{line} | "
            "{message}"
        )


def create_file_formatter(include_context: bool = True) -> str:
    """Create a file formatter with optional context.
    
    Args:
        include_context: Whether to include module context.
        
    Returns:
        Format string for file output.
    """
    if include_context:
        return (
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
            "{level: <8} | "
            "{name}:{function}:{line} | "
            "{message}"
        )
    else:
        return (
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
            "{level: <8} | "
            "{message}"
        )


def create_json_formatter() -> Callable[[Dict[str, Any]], str]:
    """Create a JSON formatter function.
    
    Returns:
        Function that formats log records as JSON.
    """
    import json
    
    def json_formatter(record: Dict[str, Any]) -> str:
        """Format a log record as JSON.
        
        Args:
            record: Log record dictionary.
            
        Returns:
            JSON string representation of the log record.
        """
        # Extract basic fields
        log_entry = {
            "timestamp": record["time"].strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "level": record["level"].name,
            "module": record["name"],
            "function": record["function"],
            "line": record["line"],
            "message": record["message"],
        }
        
        # Add extra fields if present
        if "extra" in record:
            log_entry.update(record["extra"])
            
        return json.dumps(log_entry, default=str)
    
    return json_formatter


def create_agent_formatter() -> str:
    """Create a formatter specifically for agent operations.
    
    Returns:
        Format string optimized for agent logging.
    """
    return (
        "{time:HH:mm:ss.SSS} | "
        "<level>{level: <8}</level> | "
        "<yellow>AGENT</yellow> | "
        "<cyan>{extra[agent_step]}</cyan> | "
        "<level>{message}</level>"
    )


def create_llm_formatter() -> str:
    """Create a formatter specifically for LLM operations.
    
    Returns:
        Format string optimized for LLM logging.
    """
    return (
        "{time:HH:mm:ss.SSS} | "
        "<level>{level: <8}</level> | "
        "<magenta>LLM</magenta> | "
        "<cyan>{extra[llm_model]}</cyan> | "
        "<level>{message}</level>"
    )


def create_graph_formatter() -> str:
    """Create a formatter specifically for graph operations.
    
    Returns:
        Format string optimized for graph logging.
    """
    return (
        "{time:HH:mm:ss.SSS} | "
        "<level>{level: <8}</level> | "
        "<blue>GRAPH</blue> | "
        "<cyan>{extra[graph_operation]}</cyan> | "
        "<level>{message}</level>"
    )
