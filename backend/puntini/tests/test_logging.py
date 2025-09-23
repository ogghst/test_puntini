"""Tests for the logging system to ensure no duplicate messages."""

import logging
import tempfile
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from puntini.logging import setup_logging, get_logger, LoggingService
from puntini.utils.settings import Settings


class TestLoggingSystem:
    """Test cases for the logging system."""
    
    def test_logging_service_singleton(self):
        """Test that logging service is properly managed as singleton."""
        # Clear global state
        import puntini.logging.logger as logger_module
        logger_module._logging_service = None
        
        # Setup logging
        settings = Settings()
        service1 = setup_logging(settings)
        service2 = setup_logging(settings)
        
        # Should be the same instance
        assert service1 is service2, "Logging service should be singleton"
    
    def test_multiple_logger_instances(self):
        """Test that multiple logger instances work correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('puntini.logging.logger.Settings') as mock_settings:
                mock_instance = mock_settings.return_value
                mock_instance.logging.logs_path = temp_dir
                mock_instance.logging.log_file = "test.log"
                mock_instance.logging.log_level = "info"
                mock_instance.logging.console_logging = False  # Disable console for cleaner test
                mock_instance.logging.max_bytes = 1024 * 1024
                mock_instance.logging.backup_count = 5
                
                # Setup logging
                setup_logging(mock_instance)
                
                # Create multiple loggers
                loggers = []
                for i in range(5):
                    logger = get_logger(f"test.module{i}")
                    loggers.append(logger)
                
                # Log messages from each logger
                for i, logger in enumerate(loggers):
                    logger.info(f"Message from logger {i}")
                
                # Verify all messages are in log file
                log_file = Path(temp_dir) / "test.log"
                log_content = log_file.read_text()
                
                for i in range(5):
                    message = f"Message from logger {i}"
                    count = log_content.count(message)
                    assert count == 1, f"Message '{message}' appears {count} times, should be 1"
    
    def test_no_duplicate_messages_in_file(self):
        """Test that messages are not duplicated in log files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('puntini.logging.logger.Settings') as mock_settings:
                mock_instance = mock_settings.return_value
                mock_instance.logging.logs_path = temp_dir
                mock_instance.logging.log_file = "test.log"
                mock_instance.logging.log_level = "info"
                mock_instance.logging.console_logging = False  # Disable console for cleaner test
                mock_instance.logging.max_bytes = 1024 * 1024
                mock_instance.logging.backup_count = 5
                
                # Setup logging multiple times (should not create duplicates)
                setup_logging(mock_instance)
                setup_logging(mock_instance)  # Second call should not create duplicates
                
                # Get loggers
                logger1 = get_logger("test.module1")
                logger2 = get_logger("test.module2")
                
                # Test logging
                logger1.info("Test message 1")
                logger2.info("Test message 2")
                
                # Verify log file exists and contains messages
                log_file = Path(temp_dir) / "test.log"
                assert log_file.exists(), "Log file should exist"
                
                # Read log content
                log_content = log_file.read_text()
                assert "Test message 1" in log_content
                assert "Test message 2" in log_content
                
                # Count occurrences of each message (should be 1 each)
                count1 = log_content.count("Test message 1")
                count2 = log_content.count("Test message 2")
                
                assert count1 == 1, f"Message 1 appears {count1} times, should be 1"
                assert count2 == 1, f"Message 2 appears {count2} times, should be 1"


if __name__ == "__main__":
    # Run a simple test
    test = TestLoggingSystem()
    test.test_logging_service_singleton()
    test.test_multiple_logger_instances()
    test.test_no_duplicate_messages_in_file()
    print("All logging tests passed!")
