"""Main logging service implementation using Loguru.

This module provides a comprehensive logging service with support for:
- Structured logging with context
- File rotation and retention
- Console and file output
- JSON formatting for production
- Performance optimization
"""

import sys
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union
from loguru import logger
from datetime import datetime

from ..settings import Settings


class LoggingService:
    """Centralized logging service using Loguru.
    
    This service provides structured logging with support for multiple
    output formats, file rotation, and context-aware logging.
    """
    
    def __init__(self, settings: Optional[Settings] = None):
        """Initialize the logging service.
        
        Args:
            settings: Settings instance for configuration. If None,
                     uses the global settings instance.
        """
        self.settings = settings or Settings()
        self._configured = False
        self._handlers = []
        
    def setup(self) -> None:
        """Configure the logging service based on settings.
        
        This method sets up file and console handlers with appropriate
        formatting and rotation policies.
        """
        if self._configured:
            return
            
        # Remove default handler
        logger.remove()
        
        # Create logs directory if it doesn't exist
        logs_path = Path(self.settings.logging.logs_path)
        try:
            logs_path.mkdir(parents=True, exist_ok=True)
        except (PermissionError, OSError) as e:
            # If we can't create the directory, use a fallback
            import tempfile
            logs_path = Path(tempfile.gettempdir()) / "puntini_logs"
            logs_path.mkdir(parents=True, exist_ok=True)
        
        # Setup handlers
        self._setup_file_handler(logs_path)
        
        if self.settings.logging.console_logging:
            self._setup_console_handler()
            
        self._configured = True
        
    def _setup_file_handler(self, logs_path: Path) -> None:
        """Setup file handler with rotation and retention.
        
        Args:
            logs_path: Path to the logs directory.
        """
        log_file = logs_path / self.settings.logging.log_file
        
        # File handler with rotation
        handler_id = logger.add(
            str(log_file),
            level=self.settings.logging.log_level,
            format=self._get_file_format(),
            rotation=f"{self.settings.logging.max_bytes // (1024 * 1024)} MB",
            retention=f"{self.settings.logging.backup_count} days",
            compression="zip",
            enqueue=True,  # Thread-safe logging
            backtrace=True,
            diagnose=True,
            serialize=False,  # Use structured format instead of JSON
        )
        self._handlers.append(handler_id)
        
        # Error file handler
        error_file = logs_path / "error.log"
        error_handler_id = logger.add(
            str(error_file),
            level="ERROR",
            format=self._get_file_format(),
            rotation=f"{self.settings.logging.max_bytes // (1024 * 1024)} MB",
            retention=f"{self.settings.logging.backup_count} days",
            compression="zip",
            enqueue=True,
            backtrace=True,
            diagnose=True,
            filter=lambda record: record["level"].name in ["ERROR", "CRITICAL"],
        )
        self._handlers.append(error_handler_id)
        
    def _setup_console_handler(self) -> None:
        """Setup console handler for development."""
        console_handler_id = logger.add(
            sys.stderr,
            level=self.settings.logging.log_level,
            format=self._get_console_format(),
            colorize=True,
            backtrace=True,
            diagnose=True,
        )
        self._handlers.append(console_handler_id)
        
    def _get_file_format(self) -> str:
        """Get format string for file logging.
        
        Returns:
            Format string for structured file logging.
        """
        return (
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
            "{level: <8} | "
            "{name}:{function}:{line} | "
            "{message}"
        )
        
    def _get_console_format(self) -> str:
        """Get format string for console logging.
        
        Returns:
            Format string for colored console logging.
        """
        return (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )
        
    def get_logger(self, name: str) -> Any:
        """Get a logger instance for a specific module.
        
        Args:
            name: Name of the module (usually __name__).
            
        Returns:
            Logger instance bound to the module name.
        """
        if not self._configured:
            self.setup()
        return logger.bind(module=name)
        
    def add_context(self, **kwargs: Any) -> Any:
        """Add context to the current logger.
        
        Args:
            **kwargs: Context variables to add.
            
        Returns:
            Logger instance with added context.
        """
        return logger.bind(**kwargs)
        
    def log_function_call(self, func_name: str, **kwargs: Any) -> Any:
        """Log a function call with parameters.
        
        Args:
            func_name: Name of the function being called.
            **kwargs: Function parameters and context.
            
        Returns:
            Logger instance with function context.
        """
        return logger.bind(
            function=func_name,
            call_type="function",
            **kwargs
        )
        
    def log_agent_step(self, step: str, state: Dict[str, Any], **kwargs: Any) -> Any:
        """Log an agent execution step.
        
        Args:
            step: Name of the agent step.
            state: Current agent state.
            **kwargs: Additional context.
            
        Returns:
            Logger instance with agent context.
        """
        return logger.bind(
            agent_step=step,
            call_type="agent",
            state_keys=list(state.keys()) if state else [],
            **kwargs
        )
        
    def log_llm_call(self, model: str, prompt_length: int, **kwargs: Any) -> Any:
        """Log an LLM API call.
        
        Args:
            model: Name of the LLM model.
            prompt_length: Length of the prompt.
            **kwargs: Additional context.
            
        Returns:
            Logger instance with LLM context.
        """
        return logger.bind(
            llm_model=model,
            prompt_length=prompt_length,
            call_type="llm",
            **kwargs
        )
        
    def log_graph_operation(self, operation: str, **kwargs: Any) -> Any:
        """Log a graph database operation.
        
        Args:
            operation: Type of graph operation.
            **kwargs: Additional context.
            
        Returns:
            Logger instance with graph context.
        """
        return logger.bind(
            graph_operation=operation,
            call_type="graph",
            **kwargs
        )
        
    def cleanup(self) -> None:
        """Clean up logging handlers."""
        for handler_id in self._handlers:
            logger.remove(handler_id)
        self._handlers.clear()
        self._configured = False


# Global logging service instance
_logging_service: Optional[LoggingService] = None


def get_logging_service() -> LoggingService:
    """Get the global logging service instance.
    
    Returns:
        Configured logging service instance.
    """
    global _logging_service
    if _logging_service is None:
        _logging_service = LoggingService()
        _logging_service.setup()
    return _logging_service


def get_logger(name: str) -> Any:
    """Get a logger instance for a module.
    
    Args:
        name: Module name (usually __name__).
        
    Returns:
        Logger instance bound to the module.
    """
    return get_logging_service().get_logger(name)


def setup_logging(settings: Optional[Settings] = None) -> LoggingService:
    """Setup logging with the given settings.
    
    Args:
        settings: Settings instance for configuration.
        
    Returns:
        Configured logging service instance.
    """
    global _logging_service
    _logging_service = LoggingService(settings)
    _logging_service.setup()
    return _logging_service
