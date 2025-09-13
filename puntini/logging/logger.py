"""Main logging service implementation using Python standard logging.

This module provides a comprehensive logging service with support for:
- Structured logging with context
- File rotation and retention
- Console and file output
- Custom formatting for production
- Performance optimization
"""

import sys
import os
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union
from logging.handlers import RotatingFileHandler
from datetime import datetime

from ..settings import Settings
from .custom_formatter import CustomFormatter


class LoggingService:
    """Centralized logging service using Python standard logging.
    
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
        self._formatters = {}
        
    def setup(self) -> None:
        """Configure the logging service based on settings.
        
        This method sets up file and console handlers with appropriate
        formatting and rotation policies.
        """
        if self._configured:
            return
            
        # Create logs directory if it doesn't exist
        logs_path = Path(self.settings.logging.logs_path)
        try:
            logs_path.mkdir(parents=True, exist_ok=True)
        except (PermissionError, OSError) as e:
            # If we can't create the directory, use a fallback
            import tempfile
            logs_path = Path(tempfile.gettempdir()) / "puntini_logs"
            logs_path.mkdir(parents=True, exist_ok=True)
        
        # Setup formatters
        self._setup_formatters()
        
        # Setup handlers
        self._setup_file_handler(logs_path)
        
        if self.settings.logging.console_logging:
            self._setup_console_handler()
            
        self._configured = True
        
    def _setup_formatters(self) -> None:
        """Setup formatters for different output types."""
        # File formatter
        self._formatters['file'] = CustomFormatter(
            fmt='%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console formatter
        self._formatters['console'] = CustomFormatter(
            fmt='%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
    def _setup_file_handler(self, logs_path: Path) -> None:
        """Setup file handler with rotation and retention.
        
        Args:
            logs_path: Path to the logs directory.
        """
        log_file = logs_path / self.settings.logging.log_file
        
        # Main file handler with rotation
        file_handler = RotatingFileHandler(
            str(log_file),
            maxBytes=self.settings.logging.max_bytes,
            backupCount=self.settings.logging.backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, self.settings.logging.log_level.upper()))
        file_handler.setFormatter(self._formatters['file'])
        
        # Error file handler
        error_file = logs_path / "error.log"
        error_handler = RotatingFileHandler(
            str(error_file),
            maxBytes=self.settings.logging.max_bytes,
            backupCount=self.settings.logging.backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(self._formatters['file'])
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.settings.logging.log_level.upper()))
        root_logger.addHandler(file_handler)
        root_logger.addHandler(error_handler)
        
        self._handlers.extend([file_handler, error_handler])
        
    def _setup_console_handler(self) -> None:
        """Setup console handler for development."""
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(getattr(logging, self.settings.logging.log_level.upper()))
        console_handler.setFormatter(self._formatters['console'])
        
        # Add to root logger
        root_logger = logging.getLogger()
        root_logger.addHandler(console_handler)
        
        self._handlers.append(console_handler)
        
    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger instance for a specific module.
        
        Args:
            name: Name of the module (usually __name__).
            
        Returns:
            Logger instance bound to the module name.
        """
        if not self._configured:
            self.setup()
        return logging.getLogger(name)
        
    def add_context(self, **kwargs: Any) -> Dict[str, Any]:
        """Add context to the current logger.
        
        Args:
            **kwargs: Context variables to add.
            
        Returns:
            Context dictionary for use with logging methods.
        """
        return kwargs
        
    def log_function_call(self, logger: logging.Logger, func_name: str, **kwargs: Any) -> None:
        """Log a function call with parameters.
        
        Args:
            logger: Logger instance to use.
            func_name: Name of the function being called.
            **kwargs: Function parameters and context.
        """
        context = {
            'function': func_name,
            'call_type': 'function',
            **kwargs
        }
        logger.info(f"Function call: {func_name}", extra=context)
        
    def log_agent_step(self, logger: logging.Logger, step: str, state: Dict[str, Any], **kwargs: Any) -> None:
        """Log an agent execution step.
        
        Args:
            logger: Logger instance to use.
            step: Name of the agent step.
            state: Current agent state.
            **kwargs: Additional context.
        """
        context = {
            'agent_step': step,
            'call_type': 'agent',
            'state_keys': list(state.keys()) if state else [],
            **kwargs
        }
        logger.info(f"Agent step: {step}", extra=context)
        
    def log_llm_call(self, logger: logging.Logger, model: str, prompt_length: int, **kwargs: Any) -> None:
        """Log an LLM API call.
        
        Args:
            logger: Logger instance to use.
            model: Name of the LLM model.
            prompt_length: Length of the prompt.
            **kwargs: Additional context.
        """
        context = {
            'llm_model': model,
            'prompt_length': prompt_length,
            'call_type': 'llm',
            **kwargs
        }
        logger.info(f"LLM call: {model}", extra=context)
        
    def log_graph_operation(self, logger: logging.Logger, operation: str, **kwargs: Any) -> None:
        """Log a graph database operation.
        
        Args:
            logger: Logger instance to use.
            operation: Type of graph operation.
            **kwargs: Additional context.
        """
        context = {
            'graph_operation': operation,
            'call_type': 'graph',
            **kwargs
        }
        logger.info(f"Graph operation: {operation}", extra=context)
        
    def cleanup(self) -> None:
        """Clean up logging handlers."""
        root_logger = logging.getLogger()
        for handler in self._handlers:
            root_logger.removeHandler(handler)
            handler.close()
        self._handlers.clear()
        self._formatters.clear()
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


def get_logger(name: str) -> logging.Logger:
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
