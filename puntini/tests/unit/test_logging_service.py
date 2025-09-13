"""Unit tests for the LoggingService implementation.

This module contains comprehensive unit tests for the LoggingService
class, testing all methods and functionality including setup, logging,
and error handling.
"""

import pytest
import tempfile
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from puntini.logging import LoggingService, get_logger, setup_logging, get_logging_service
from puntini.settings import Settings


class TestLoggingServiceInitialization:
    """Test LoggingService initialization and basic properties."""
    
    def test_initialization_with_settings(self):
        """Test that LoggingService initializes correctly with settings."""
        settings = Settings()
        logging_service = LoggingService(settings)
        
        assert isinstance(logging_service, LoggingService)
        assert logging_service.settings == settings
        assert logging_service._configured is False
        assert logging_service._handlers == []
    
    def test_initialization_without_settings(self):
        """Test that LoggingService initializes correctly without settings."""
        logging_service = LoggingService()
        
        assert isinstance(logging_service, LoggingService)
        assert logging_service.settings is not None
        assert logging_service._configured is False
        assert logging_service._handlers == []


class TestLoggingServiceSetup:
    """Test LoggingService setup functionality."""
    
    def test_setup_creates_logs_directory(self):
        """Test that setup creates the logs directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings()
            settings.logging.logs_path = temp_dir
            settings.logging.console_logging = False
            
            logging_service = LoggingService(settings)
            logging_service.setup()
            
            logs_path = Path(temp_dir)
            assert logs_path.exists()
            assert logs_path.is_dir()
    
    def test_setup_removes_default_handler(self):
        """Test that setup removes the default loguru handler."""
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings()
            settings.logging.logs_path = temp_dir
            settings.logging.console_logging = False
            
            logging_service = LoggingService(settings)
            
            # This test was for loguru, which is no longer used.
            # The new implementation doesn't remove a default handler in the same way.
            # We can check that it adds our handlers.
            with patch('logging.RootLogger.addHandler') as mock_add:
                logging_service.setup()
                assert mock_add.call_count > 0
    
    def test_setup_idempotent(self):
        """Test that setup is idempotent."""
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings()
            settings.logging.logs_path = temp_dir
            settings.logging.console_logging = False
            
            logging_service = LoggingService(settings)
            
            # First setup
            logging_service.setup()
            first_configured = logging_service._configured
            first_handlers = len(logging_service._handlers)
            
            # Second setup
            logging_service.setup()
            second_configured = logging_service._configured
            second_handlers = len(logging_service._handlers)
            
            assert first_configured == second_configured
            assert first_handlers == second_handlers
    
    def test_setup_with_console_logging(self):
        """Test setup with console logging enabled."""
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings()
            settings.logging.logs_path = temp_dir
            settings.logging.console_logging = True
            
            logging_service = LoggingService(settings)
            
            with patch('logging.RootLogger.addHandler') as mock_add:
                logging_service.setup()
                
                # Should add file handler, error handler, and console handler
                assert mock_add.call_count >= 3


class TestLoggingServiceFileHandlers:
    """Test LoggingService file handler setup."""
    
    def test_file_handler_creation(self):
        """Test that file handlers are created correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings()
            settings.logging.logs_path = temp_dir
            settings.logging.console_logging = False
            settings.logging.log_file = "test.log"
            
            logging_service = LoggingService(settings)
            
            with patch('logging.RootLogger.addHandler') as mock_add:
                logging_service.setup()
                
                # Should add main log file and error log file
                assert mock_add.call_count >= 2
                
                # Check that file paths are correct
                calls = mock_add.call_args_list
                handler_files = [h.baseFilename for call in calls for h in call.args if hasattr(h, 'baseFilename')]
                assert any("test.log" in str(path) for path in handler_files)
                assert any("error.log" in str(path) for path in handler_files)
    
    def test_file_handler_rotation_configuration(self):
        """Test that file handlers use correct rotation configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings()
            settings.logging.logs_path = temp_dir
            settings.logging.console_logging = False
            settings.logging.max_bytes = 10485760  # 10MB
            settings.logging.backup_count = 5
            
            logging_service = LoggingService(settings)
            
            with patch('logging.RootLogger.addHandler') as mock_add:
                logging_service.setup()
                
                # Check rotation and retention settings
                calls = mock_add.call_args_list
                for call in calls:
                    handler = call.args[0]
                    if isinstance(handler, logging.handlers.RotatingFileHandler):
                        assert handler.maxBytes == 10485760
                        assert handler.backupCount == 5


class TestLoggingServiceConsoleHandlers:
    """Test LoggingService console handler setup."""
    
    def test_console_handler_creation_when_enabled(self):
        """Test that console handler is created when enabled."""
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings()
            settings.logging.logs_path = temp_dir
            settings.logging.console_logging = True
            
            logging_service = LoggingService(settings)
            
            with patch('logging.RootLogger.addHandler') as mock_add:
                logging_service.setup()
                
                # Should add console handler
                calls = mock_add.call_args_list
                console_handlers = [h for call in calls for h in call.args if isinstance(h, logging.StreamHandler) and not hasattr(h, 'baseFilename')]
                assert len(console_handlers) > 0
    
    def test_console_handler_not_created_when_disabled(self):
        """Test that console handler is not created when disabled."""
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings()
            settings.logging.logs_path = temp_dir
            settings.logging.console_logging = False
            
            logging_service = LoggingService(settings)
            
            with patch('logging.RootLogger.addHandler') as mock_add:
                logging_service.setup()
                
                # Should not add console handler
                calls = mock_add.call_args_list
                console_handlers = [h for call in calls for h in call.args if isinstance(h, logging.StreamHandler) and not hasattr(h, 'baseFilename')]
                assert len(console_handlers) == 0


class TestLoggingServiceLoggerCreation:
    """Test LoggingService logger creation methods."""
    
    def test_get_logger_returns_bound_logger(self):
        """Test that get_logger returns a logger bound to module name."""
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings()
            settings.logging.logs_path = temp_dir
            settings.logging.console_logging = False
            
            logging_service = LoggingService(settings)
            logging_service.setup()
            
            logger = logging_service.get_logger("test_module")
            
            # Should return a logger instance
            assert logger is not None
            assert hasattr(logger, 'info')
            assert hasattr(logger, 'debug')
            assert hasattr(logger, 'error')
    
    def test_get_logger_auto_setup(self):
        """Test that get_logger automatically sets up if not configured."""
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings()
            settings.logging.logs_path = temp_dir
            settings.logging.console_logging = False
            
            logging_service = LoggingService(settings)
            
            # Should auto-setup when getting logger
            logger = logging_service.get_logger("test_module")
            assert logging_service._configured is True
            assert logger is not None


class TestLoggingServiceContextMethods:
    """Test LoggingService context-specific logging methods."""
    
    def test_add_context(self):
        """Test adding context to logger."""
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings()
            settings.logging.logs_path = temp_dir
            settings.logging.console_logging = False
            
            logging_service = LoggingService(settings)
            logging_service.setup()
            
            context = logging_service.add_context(user_id="123", action="test")
            
            assert context is not None
            assert context == {"user_id": "123", "action": "test"}
    
    def test_log_function_call(self):
        """Test logging function calls."""
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings()
            settings.logging.logs_path = temp_dir
            settings.logging.console_logging = False
            
            logging_service = LoggingService(settings)
            logging_service.setup()
            
            logger = get_logger("test_module")
            with patch.object(logger, 'info') as mock_info:
                logging_service.log_function_call(
                    logger,
                    func_name="test_function",
                    param1="value1",
                    param2="value2"
                )
                mock_info.assert_called_once()
    
    def test_log_agent_step(self):
        """Test logging agent steps."""
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings()
            settings.logging.logs_path = temp_dir
            settings.logging.console_logging = False
            
            logging_service = LoggingService(settings)
            logging_service.setup()
            
            logger = get_logger("test_module")
            with patch.object(logger, 'info') as mock_info:
                logging_service.log_agent_step(
                    logger,
                    step="parse_goal",
                    state={"goal": "test", "attempt": 1},
                    complexity="simple"
                )
                mock_info.assert_called_once()
    
    def test_log_llm_call(self):
        """Test logging LLM calls."""
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings()
            settings.logging.logs_path = temp_dir
            settings.logging.console_logging = False
            
            logging_service = LoggingService(settings)
            logging_service.setup()
            
            logger = get_logger("test_module")
            with patch.object(logger, 'info') as mock_info:
                logging_service.log_llm_call(
                    logger,
                    model="gpt-4",
                    prompt_length=150,
                    temperature=0.1
                )
                mock_info.assert_called_once()
    
    def test_log_graph_operation(self):
        """Test logging graph operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings()
            settings.logging.logs_path = temp_dir
            settings.logging.console_logging = False
            
            logging_service = LoggingService(settings)
            logging_service.setup()
            
            logger = get_logger("test_module")
            with patch.object(logger, 'info') as mock_info:
                logging_service.log_graph_operation(
                    logger,
                    operation="create_node",
                    node_type="User",
                    properties={"name": "John"}
                )
                mock_info.assert_called_once()


class TestLoggingServiceCleanup:
    """Test LoggingService cleanup functionality."""
    
    def test_cleanup_removes_handlers(self):
        """Test that cleanup removes all handlers."""
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings()
            settings.logging.logs_path = temp_dir
            settings.logging.console_logging = False
            
            logging_service = LoggingService(settings)
            logging_service.setup()
            
            initial_handlers = len(logging_service._handlers)
            assert initial_handlers > 0
            
            with patch('logging.RootLogger.removeHandler') as mock_remove:
                logging_service.cleanup()
                
                # Should remove all handlers
                assert mock_remove.call_count == initial_handlers
                assert len(logging_service._handlers) == 0
                assert logging_service._configured is False


class TestGlobalLoggingFunctions:
    """Test global logging functions."""
    
    def test_get_logging_service_singleton(self):
        """Test that get_logging_service returns singleton instance."""
        service1 = get_logging_service()
        service2 = get_logging_service()
        
        assert service1 is service2
        assert isinstance(service1, LoggingService)
    
    def test_get_logger_global_function(self):
        """Test the global get_logger function."""
        logger = get_logger("test_module")
        
        assert logger is not None
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'debug')
        assert hasattr(logger, 'error')
    
    def test_setup_logging_global_function(self):
        """Test the global setup_logging function."""
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings()
            settings.logging.logs_path = temp_dir
            settings.logging.console_logging = False
            
            logging_service = setup_logging(settings)
            
            assert isinstance(logging_service, LoggingService)
            assert logging_service._configured is True


import io
import logging

class TestLoggingServiceIntegration:
    """Test LoggingService integration with actual logging."""
    
    def test_error_log_includes_stack_trace(self):
        """Test that logger.error() from an except block includes a stack trace."""
        # Use a stream handler to capture log output
        log_stream = io.StringIO()

        # Create a new logging service with a custom handler
        settings = Settings()
        settings.logging.console_logging = False # Disable default console handler

        logging_service = LoggingService(settings)

        # Add our stream handler to the root logger
        stream_handler = logging.StreamHandler(log_stream)

        # Use the custom formatter to match the service's configuration
        formatter = logging_service._formatters.get('console')
        if formatter:
            stream_handler.setFormatter(formatter)

        root_logger = logging.getLogger()
        root_logger.addHandler(stream_handler)

        logger = logging_service.get_logger("test_exception")

        try:
            raise ValueError("This is a test exception")
        except ValueError:
            logger.exception("An error occurred")

        # Clean up the handler
        root_logger.removeHandler(stream_handler)

        log_output = log_stream.getvalue()

        assert "An error occurred" in log_output
        assert "Traceback (most recent call last):" in log_output
        assert 'raise ValueError("This is a test exception")' in log_output

    def test_basic_logging_functionality(self):
        """Test that basic logging works correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings()
            settings.logging.logs_path = temp_dir
            settings.logging.console_logging = False
            
            logging_service = LoggingService(settings)
            logging_service.setup()
            
            logger = logging_service.get_logger("test_module")
            
            # Test different log levels
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")
            
            # Verify log files were created
            logs_path = Path(temp_dir)
            log_files = list(logs_path.glob("*.log"))
            assert len(log_files) > 0
    
    def test_structured_logging_functionality(self):
        """Test that structured logging works correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings()
            settings.logging.logs_path = temp_dir
            settings.logging.console_logging = False
            
            logging_service = LoggingService(settings)
            logging_service.setup()
            
            logger = logging_service.get_logger("test_module")
            
            # Test structured logging
            extra_data = {
                "user_id": "12345",
                "action": "login",
                "ip_address": "192.168.1.1",
                "success": True
            }
            with patch.object(logger, '_log') as mock_log:
                logger.info("User action performed", extra=extra_data)
                mock_log.assert_called_once()

            # Verify log files were created
            logs_path = Path(temp_dir)
            log_files = list(logs_path.glob("*.log"))
            assert len(log_files) > 0
    
    def test_agent_specific_logging_functionality(self):
        """Test that agent-specific logging works correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings()
            settings.logging.logs_path = temp_dir
            settings.logging.console_logging = False
            
            logging_service = LoggingService(settings)
            logging_service.setup()
            
            logger = get_logger("test_module")
            with patch.object(logger, 'info') as mock_info:
                # Test agent step logging
                logging_service.log_agent_step(
                    logger,
                    step="parse_goal",
                    state={"goal": "Create a user node", "attempt": 1},
                    complexity="simple"
                )

                # Test LLM call logging
                logging_service.log_llm_call(
                    logger,
                    model="gpt-4",
                    prompt_length=150,
                    temperature=0.1
                )

                # Test graph operation logging
                logging_service.log_graph_operation(
                    logger,
                    operation="create_node",
                    node_type="User",
                    properties={"name": "John"}
                )

                assert mock_info.call_count == 3
            
            # Verify log files were created
            logs_path = Path(temp_dir)
            log_files = list(logs_path.glob("*.log"))
            assert len(log_files) > 0


class TestLoggingServiceErrorHandling:
    """Test LoggingService error handling."""
    
    def test_logger_creation_without_setup(self):
        """Test logger creation without prior setup."""
        logging_service = LoggingService()
        
        # Should auto-setup when getting logger
        logger = logging_service.get_logger("test_module")
        assert logger is not None
        assert logging_service._configured is True




@pytest.fixture
def temp_logging_service():
    """Fixture providing a LoggingService with temporary directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        settings = Settings()
        settings.logging.logs_path = temp_dir
        settings.logging.console_logging = False
        
        logging_service = LoggingService(settings)
        logging_service.setup()
        
        yield logging_service, temp_dir


@pytest.fixture
def sample_settings():
    """Fixture providing sample settings for testing."""
    settings = Settings()
    settings.logging.log_level = "DEBUG"
    settings.logging.console_logging = True
    settings.logging.max_bytes = 10485760
    settings.logging.backup_count = 5
    settings.logging.log_file = "test.log"
    settings.logging.logs_path = "test_logs"
    return settings
