"""No-op tracer implementation.

This module provides a no-op implementation of the Tracer interface
for testing and when observability is not needed.
"""

from contextlib import AbstractContextManager
from typing import Any
from ..interfaces.tracer import Tracer


class NoOpTracer:
    """No-op implementation of Tracer.
    
    This implementation provides all the Tracer interface methods
    but does not perform any actual tracing or logging.
    """
    
    def start_trace(self, name: str, trace_id: str | None = None) -> AbstractContextManager:
        """Start a new trace for agent execution.

        Args:
            name: Name of the trace.
            trace_id: Optional trace ID (ignored).

        Returns:
            Context manager for the trace.
        """
        return NoOpContextManager()
    
    def start_span(self, name: str, parent: Any | None = None) -> AbstractContextManager:
        """Start a new span within a trace.

        Args:
            name: Name of the span.
            parent: Parent span or trace (ignored).

        Returns:
            Context manager for the span.
        """
        return NoOpContextManager()
    
    def log_io(self, input_data: Any, output_data: Any) -> None:
        """Log input/output data for a span.

        Args:
            input_data: Input data to log (ignored).
            output_data: Output data to log (ignored).
        """
        pass
    
    def log_decision(self, decision: str, context: dict[str, Any]) -> None:
        """Log a decision point in the execution.

        Args:
            decision: Decision that was made (ignored).
            context: Context information for the decision (ignored).
        """
        pass
    
    def flush(self) -> None:
        """Flush all pending trace data.
        
        No-op implementation does nothing.
        """
        pass


class NoOpContextManager(AbstractContextManager):
    """No-op context manager for traces and spans."""
    
    def __enter__(self):
        """Enter the context."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context."""
        pass
    
    def log_io(self, input_data: Any, output_data: Any) -> None:
        """Log input/output data for this context.
        
        Args:
            input_data: Input data to log (ignored).
            output_data: Output data to log (ignored).
        """
        pass
    
    def log_decision(self, decision: str, context: dict[str, Any]) -> None:
        """Log a decision point in this context.
        
        Args:
            decision: Decision that was made (ignored).
            context: Context information for the decision (ignored).
        """
        pass