# Logging System

This directory contains a comprehensive logging system built on top of Loguru, designed specifically for the agent system with structured logging, context awareness, and multiple output formats.

## Features

- **Structured Logging**: JSON and key-value pair logging for easy parsing
- **Context Awareness**: Automatic context binding for different operation types
- **File Rotation**: Automatic log file rotation with compression
- **Multiple Handlers**: Separate handlers for different log levels and purposes
- **Performance Optimized**: Asynchronous logging for better performance
- **Development Friendly**: Colored console output and detailed debugging

## Quick Start

```python
from puntini.logging import get_logger, setup_logging
from puntini.utils.settings import Settings

# Setup logging
settings = Settings()
setup_logging(settings)

# Get a logger
logger = get_logger(__name__)

# Basic logging
logger.info("Application started")
logger.error("Something went wrong", error_code=500)
```

## Configuration

The logging system is configured through the `config.json` file:

```json
{
  "logging": {
    "log_level": "DEBUG",
    "console_logging": false,
    "max_bytes": 10485760,
    "backup_count": 5,
    "log_file": "backend.log",
    "logs_path": "logs"
  }
}
```

### Configuration Options

- `log_level`: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `console_logging`: Enable console output (useful for development)
- `max_bytes`: Maximum file size before rotation (in bytes)
- `backup_count`: Number of backup files to keep
- `log_file`: Main log file name
- `logs_path`: Directory for log files

## Usage Patterns

### Basic Logging

```python
from puntini.logging import get_logger

logger = get_logger(__name__)

# Simple messages
logger.info("User logged in")
logger.error("Database connection failed")

# With context
logger.info("Order processed", order_id=12345, amount=99.99)
```

### Agent-Specific Logging

```python
from puntini.logging import get_logging_service

logging_service = get_logging_service()

# Agent step logging
agent_logger = logging_service.log_agent_step(
    step="parse_goal",
    state={"goal": "Create user", "attempt": 1}
)
agent_logger.info("Processing agent step")

# LLM call logging
llm_logger = logging_service.log_llm_call(
    model="gpt-4",
    prompt_length=150
)
llm_logger.info("Making LLM API call")

# Graph operation logging
graph_logger = logging_service.log_graph_operation(
    operation="create_node",
    node_type="User"
)
graph_logger.info("Creating graph node")
```

### Function Call Logging

```python
from puntini.logging import get_logging_service

logging_service = get_logging_service()

# Log function calls with parameters
func_logger = logging_service.log_function_call(
    func_name="parse_goal",
    goal="Create a user node",
    attempt=1
)
func_logger.info("Function called")
```

## Log Files

The system creates several log files:

- `backend.log`: Main application log
- `error.log`: Error-level messages only
- `agent.log`: Agent-specific operations
- `llm.log`: LLM API calls
- `graph.log`: Graph database operations

## Formatters

Different formatters are available for different scenarios:

- **Development**: Colored console output with full context
- **Production**: Clean file output with timestamps
- **JSON**: Structured JSON for log aggregation
- **Minimal**: Simple format for testing

## Handlers

The system supports multiple handlers:

- **Console**: Colored output for development
- **File**: Rotating file output with compression
- **Error File**: Separate error-only log file
- **JSON**: Structured JSON output for production

## Best Practices

1. **Use Structured Logging**: Always include relevant context in log messages
2. **Choose Appropriate Levels**: Use DEBUG for development, INFO for normal operations, ERROR for failures
3. **Include Context**: Add relevant parameters and state information
4. **Use Specific Loggers**: Use agent, LLM, and graph-specific loggers for better organization
5. **Handle Exceptions**: Always log exceptions with full context

## Examples

See `logging_example.py` in the project root for a complete demonstration of the logging system.

## Performance

The logging system is optimized for performance:

- Asynchronous logging by default (`enqueue=True`)
- Efficient file rotation with compression
- Minimal overhead for disabled log levels
- Thread-safe operations

## Troubleshooting

### Logs Not Appearing

1. Check the log level configuration
2. Verify the logs directory exists and is writable
3. Check console logging is enabled if expecting console output

### Performance Issues

1. Ensure `enqueue=True` is set for file handlers
2. Consider reducing log level in production
3. Check disk space for log files

### Import Errors

1. Ensure loguru is installed: `pip install loguru`
2. Check Python path includes the project root
3. Verify all dependencies are installed
