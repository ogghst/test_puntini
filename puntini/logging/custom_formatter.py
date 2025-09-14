import json
import logging
import sys

class CustomFormatter(logging.Formatter):
    """
    Custom log formatter that adds stack trace information to ERROR and CRITICAL logs
    if it's missing.
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Formats the log record to include a stack trace for error-level messages.

        If the record's level is ERROR or higher and it was logged from within
        an exception handler (`sys.exc_info()` is not None), this method ensures
        that the exception information is added to the log message, even if
        `exc_info=True` was not passed to the logger.
        """
        if record.levelno >= logging.ERROR and not record.exc_info:
            # If we are in an exception handler, add the exception info
            if sys.exc_info() != (None, None, None):
                record.exc_info = sys.exc_info()
                
        message = super().format(record)
        
        # Extract extra attributes
        extra_data = {}
        for key, value in record.__dict__.items():
            if key not in ['args', 'asctime', 'created', 'exc_info', 'exc_text', 
                          'filename', 'funcName', 'levelname', 'levelno', 'lineno', 
                          'module', 'msecs', 'message', 'msg', 'name', 'pathname', 
                          'process', 'processName', 'relativeCreated', 'stack_info', 
                          'thread', 'threadName']:
                extra_data[key] = value
        
        if extra_data:
            message =  f"{message} - {json.dumps(extra_data)}"

        return message
