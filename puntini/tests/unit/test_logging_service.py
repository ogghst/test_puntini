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
            
            # Mock logger.remove to verify it's called
            with patch('puntini.logging.logger.logger.remove') as mock_remove:
                logging_service.setup()
                mock_remove.assert_called_once()
    
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
            
            with patch('puntini.logging.logger.logger.add') as mock_add:
                logging_service.setup()
                
                # Should add file handler and console handler
                assert mock_add.call_count >= 2


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
            
            with patch('puntini.logging.logger.logger.add') as mock_add:
                logging_service.setup()
                
                # Should add main log file and error log file
                assert mock_add.call_count >= 2
                
                # Check that file paths are correct
                calls = mock_add.call_args_list
                file_paths = [call[0][0] for call in calls]
                assert any("test.log" in str(path) for path in file_paths)
                assert any("error.log" in str(path) for path in file_paths)
    
    def test_file_handler_rotation_configuration(self):
        """Test that file handlers use correct rotation configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings()
            settings.logging.logs_path = temp_dir
            settings.logging.console_logging = False
            settings.logging.max_bytes = 10485760  # 10MB
            settings.logging.backup_count = 5
            
            logging_service = LoggingService(settings)
            
            with patch('puntini.logging.logger.logger.add') as mock_add:
                logging_service.setup()
                
                # Check rotation and retention settings
                calls = mock_add.call_args_list
                for call in calls:
                    kwargs = call[1]
                    if 'rotation' in kwargs:
                        assert "10 MB" in kwargs['rotation']
                    if 'retention' in kwargs:
                        assert "5 days" in kwargs['retention']


class TestLoggingServiceConsoleHandlers:
    """Test LoggingService console handler setup."""
    
    def test_console_handler_creation_when_enabled(self):
        """Test that console handler is created when enabled."""
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings()
            settings.logging.logs_path = temp_dir
            settings.logging.console_logging = True
            
            logging_service = LoggingService(settings)
            
            with patch('puntini.logging.logger.logger.add') as mock_add:
                logging_service.setup()
                
                # Should add console handler
                calls = mock_add.call_args_list
                console_calls = [call for call in calls if call[1].get('colorize') is True]
                assert len(console_calls) > 0
    
    def test_console_handler_not_created_when_disabled(self):
        """Test that console handler is not created when disabled."""
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings()
            settings.logging.logs_path = temp_dir
            settings.logging.console_logging = False
            
            logging_service = LoggingService(settings)
            
            with patch('puntini.logging.logger.logger.add') as mock_add:
                logging_service.setup()
                
                # Should not add console handler
                calls = mock_add.call_args_list
                console_calls = [call for call in calls if call[1].get('colorize') is True]
                assert len(console_calls) == 0


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
            
            context_logger = logging_service.add_context(user_id="123", action="test")
            
            assert context_logger is not None
            assert hasattr(context_logger, 'info')
    
    def test_log_function_call(self):
        """Test logging function calls."""
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings()
            settings.logging.logs_path = temp_dir
            settings.logging.console_logging = False
            
            logging_service = LoggingService(settings)
            logging_service.setup()
            
            func_logger = logging_service.log_function_call(
                func_name="test_function",
                param1="value1",
                param2="value2"
            )
            
            assert func_logger is not None
            assert hasattr(func_logger, 'info')
    
    def test_log_agent_step(self):
        """Test logging agent steps."""
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings()
            settings.logging.logs_path = temp_dir
            settings.logging.console_logging = False
            
            logging_service = LoggingService(settings)
            logging_service.setup()
            
            agent_logger = logging_service.log_agent_step(
                step="parse_goal",
                state={"goal": "test", "attempt": 1},
                complexity="simple"
            )
            
            assert agent_logger is not None
            assert hasattr(agent_logger, 'info')
    
    def test_log_llm_call(self):
        """Test logging LLM calls."""
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings()
            settings.logging.logs_path = temp_dir
            settings.logging.console_logging = False
            
            logging_service = LoggingService(settings)
            logging_service.setup()
            
            llm_logger = logging_service.log_llm_call(
                model="gpt-4",
                prompt_length=150,
                temperature=0.1
            )
            
            assert llm_logger is not None
            assert hasattr(llm_logger, 'info')
    
    def test_log_graph_operation(self):
        """Test logging graph operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings()
            settings.logging.logs_path = temp_dir
            settings.logging.console_logging = False
            
            logging_service = LoggingService(settings)
            logging_service.setup()
            
            graph_logger = logging_service.log_graph_operation(
                operation="create_node",
                node_type="User",
                properties={"name": "John"}
            )
            
            assert graph_logger is not None
            assert hasattr(graph_logger, 'info')


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
            
            with patch('puntini.logging.logger.logger.remove') as mock_remove:
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


class TestLoggingServiceIntegration:
    """Test LoggingService integration with actual logging."""
    
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
            logger.info(
                "User action performed",
                user_id="12345",
                action="login",
                ip_address="192.168.1.1",
                success=True
            )
            
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
            
            # Test agent step logging
            agent_logger = logging_service.log_agent_step(
                step="parse_goal",
                state={"goal": "Create a user node", "attempt": 1},
                complexity="simple"
            )
            agent_logger.info("Processing agent step")
            
            # Test LLM call logging
            llm_logger = logging_service.log_llm_call(
                model="gpt-4",
                prompt_length=150,
                temperature=0.1
            )
            llm_logger.info("Making LLM API call")
            
            # Test graph operation logging
            graph_logger = logging_service.log_graph_operation(
                operation="create_node",
                node_type="User",
                properties={"name": "John"}
            )
            graph_logger.info("Executing graph operation")
            
            # Verify log files were created
            logs_path = Path(temp_dir)
            log_files = list(logs_path.glob("*.log"))
            assert len(log_files) > 0


class TestLoggingServiceErrorHandling:
    """Test LoggingService error handling."""
    
    def test_setup_with_invalid_logs_path(self):
        """Test setup with invalid logs path."""
        settings = Settings()
        settings.logging.logs_path = "/invalid/path/that/does/not/exist"
        settings.logging.console_logging = False
        
        logging_service = LoggingService(settings)
        
        # Should handle invalid path gracefully by using fallback
        with patch('pathlib.Path.mkdir') as mock_mkdir:
            # First call fails, second call (fallback) succeeds
            mock_mkdir.side_effect = [PermissionError("Permission denied"), None]
            
            # Should not raise exception and should use fallback
            logging_service.setup()
            
            # Should have called mkdir twice (original + fallback)
            assert mock_mkdir.call_count == 2
    
    def test_logger_creation_without_setup(self):
        """Test logger creation without prior setup."""
        logging_service = LoggingService()
        
        # Should auto-setup when getting logger
        logger = logging_service.get_logger("test_module")
        assert logger is not None
        assert logging_service._configured is True


class TestLoggingServiceFormatters:
    """Test LoggingService formatter methods."""
    
    def test_file_format(self):
        """Test file format string."""
        logging_service = LoggingService()
        format_string = logging_service._get_file_format()
        
        assert isinstance(format_string, str)
        assert "time" in format_string
        assert "level" in format_string
        assert "name" in format_string
        assert "function" in format_string
        assert "line" in format_string
        assert "message" in format_string
    
    def test_console_format(self):
        """Test console format string."""
        logging_service = LoggingService()
        format_string = logging_service._get_console_format()
        
        assert isinstance(format_string, str)
        assert "time" in format_string
        assert "level" in format_string
        assert "name" in format_string
        assert "function" in format_string
        assert "line" in format_string
        assert "message" in format_string
        # Should contain color tags
        assert "<" in format_string and ">" in format_string


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
