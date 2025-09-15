"""Logging handlers for different output destinations.

This module provides handlers for various logging scenarios including
file rotation, console output, and structured logging.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from loguru import logger

from .formatters import (
    create_console_formatter,
    create_file_formatter,
    create_json_formatter,
    create_agent_formatter,
    create_llm_formatter,
    create_graph_formatter,
)


def create_handlers() -> Dict[str, Any]:
    """Create handler configurations for different scenarios.
    
    Returns:
        Dictionary mapping handler names to configurations.
    """
    return {
        "console": {
            "sink": sys.stderr,
            "level": "DEBUG",
            "format": create_console_formatter(),
            "colorize": True,
            "backtrace": True,
            "diagnose": True,
        },
        "file": {
            "sink": "app.log",
            "level": "INFO",
            "format": create_file_formatter(),
            "rotation": "10 MB",
            "retention": "7 days",
            "compression": "zip",
            "enqueue": True,
        },
        "error_file": {
            "sink": "error.log",
            "level": "ERROR",
            "format": create_file_formatter(),
            "rotation": "5 MB",
            "retention": "30 days",
            "compression": "zip",
            "enqueue": True,
        },
        "json": {
            "sink": "app.json",
            "level": "INFO",
            "format": create_json_formatter(),
            "serialize": True,
            "rotation": "10 MB",
            "retention": "7 days",
            "enqueue": True,
        },
    }


def create_agent_handlers(logs_dir: Path) -> List[Dict[str, Any]]:
    """Create handlers specifically for agent operations.
    
    Args:
        logs_dir: Directory to store log files.
        
    Returns:
        List of handler configurations for agent logging.
    """
    return [
        {
            "sink": str(logs_dir / "agent.log"),
            "level": "DEBUG",
            "format": create_agent_formatter(),
            "rotation": "10 MB",
            "retention": "7 days",
            "compression": "zip",
            "enqueue": True,
            "filter": lambda record: record.get("extra", {}).get("call_type") == "agent",
        },
        {
            "sink": str(logs_dir / "llm.log"),
            "level": "DEBUG",
            "format": create_llm_formatter(),
            "rotation": "10 MB",
            "retention": "7 days",
            "compression": "zip",
            "enqueue": True,
            "filter": lambda record: record.get("extra", {}).get("call_type") == "llm",
        },
        {
            "sink": str(logs_dir / "graph.log"),
            "level": "DEBUG",
            "format": create_graph_formatter(),
            "rotation": "10 MB",
            "retention": "7 days",
            "compression": "zip",
            "enqueue": True,
            "filter": lambda record: record.get("extra", {}).get("call_type") == "graph",
        },
    ]


def create_development_handlers() -> List[Dict[str, Any]]:
    """Create handlers for development environment.
    
    Returns:
        List of handler configurations for development.
    """
    return [
        {
            "sink": sys.stderr,
            "level": "DEBUG",
            "format": create_console_formatter(use_colors=True),
            "colorize": True,
            "backtrace": True,
            "diagnose": True,
        },
        {
            "sink": "debug.log",
            "level": "DEBUG",
            "format": create_file_formatter(include_context=True),
            "rotation": "5 MB",
            "retention": "3 days",
            "enqueue": False,  # Synchronous for debugging
        },
    ]


def create_production_handlers(logs_dir: Path) -> List[Dict[str, Any]]:
    """Create handlers for production environment.
    
    Args:
        logs_dir: Directory to store log files.
        
    Returns:
        List of handler configurations for production.
    """
    return [
        {
            "sink": str(logs_dir / "app.log"),
            "level": "INFO",
            "format": create_file_formatter(include_context=True),
            "rotation": "50 MB",
            "retention": "30 days",
            "compression": "zip",
            "enqueue": True,
        },
        {
            "sink": str(logs_dir / "error.log"),
            "level": "ERROR",
            "format": create_file_formatter(include_context=True),
            "rotation": "20 MB",
            "retention": "90 days",
            "compression": "zip",
            "enqueue": True,
        },
        {
            "sink": str(logs_dir / "app.json"),
            "level": "INFO",
            "format": create_json_formatter(),
            "serialize": True,
            "rotation": "50 MB",
            "retention": "30 days",
            "enqueue": True,
        },
    ]


def create_test_handlers() -> List[Dict[str, Any]]:
    """Create handlers for testing environment.
    
    Returns:
        List of handler configurations for testing.
    """
    return [
        {
            "sink": sys.stderr,
            "level": "WARNING",
            "format": create_console_formatter(use_colors=False),
            "colorize": False,
            "backtrace": False,
            "diagnose": False,
        },
    ]


def setup_handlers(
    handlers: List[Dict[str, Any]], 
    remove_existing: bool = True
) -> List[int]:
    """Setup logging handlers.
    
    Args:
        handlers: List of handler configurations.
        remove_existing: Whether to remove existing handlers first.
        
    Returns:
        List of handler IDs for later removal.
    """
    handler_ids = []
    
    if remove_existing:
        logger.remove()
    
    for handler_config in handlers:
        handler_id = logger.add(**handler_config)
        handler_ids.append(handler_id)
    
    return handler_ids


def create_rotating_file_handler(
    file_path: str,
    level: str = "INFO",
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    compression: Optional[str] = "zip",
    **kwargs: Any
) -> Dict[str, Any]:
    """Create a rotating file handler configuration.
    
    Args:
        file_path: Path to the log file.
        level: Minimum log level.
        max_bytes: Maximum file size before rotation.
        backup_count: Number of backup files to keep.
        compression: Compression format for rotated files.
        **kwargs: Additional handler parameters.
        
    Returns:
        Handler configuration dictionary.
    """
    config = {
        "sink": file_path,
        "level": level,
        "format": create_file_formatter(),
        "rotation": f"{max_bytes // (1024 * 1024)} MB",
        "retention": f"{backup_count} days",
        "enqueue": True,
        **kwargs
    }
    
    if compression:
        config["compression"] = compression
        
    return config


def create_time_rotating_handler(
    file_path: str,
    level: str = "INFO",
    rotation_time: str = "midnight",
    retention_days: int = 7,
    compression: Optional[str] = "zip",
    **kwargs: Any
) -> Dict[str, Any]:
    """Create a time-based rotating file handler configuration.
    
    Args:
        file_path: Path to the log file.
        level: Minimum log level.
        rotation_time: Time when rotation should occur.
        retention_days: Number of days to keep log files.
        compression: Compression format for rotated files.
        **kwargs: Additional handler parameters.
        
    Returns:
        Handler configuration dictionary.
    """
    config = {
        "sink": file_path,
        "level": level,
        "format": create_file_formatter(),
        "rotation": rotation_time,
        "retention": f"{retention_days} days",
        "enqueue": True,
        **kwargs
    }
    
    if compression:
        config["compression"] = compression
        
    return config
