"""Tracer interface for observability and monitoring.

This module defines the Tracer protocol that handles tracing and monitoring
of the agent's execution for observability and debugging.
"""

from typing import Any, Protocol
from contextlib import AbstractContextManager


class Tracer(Protocol):
    """Protocol for tracing agent execution and observability.
    
    The tracer provides observability capabilities for monitoring agent
    execution, including trace creation, span management, and metrics collection.
    """
    
    def start_trace(self, name: str, trace_id: str | None = None) -> AbstractContextManager:
        """Start a new trace for agent execution.

        Args:
            name: Name of the trace.
            trace_id: Optional trace ID (generated if not provided).

        Returns:
            Context manager for the trace.

        Notes:
            Traces should be created at the beginning of agent execution
            and used to track the entire execution flow.
        """
        ...
    
    def start_span(self, name: str, parent: Any | None = None) -> AbstractContextManager:
        """Start a new span within a trace.

        Args:
            name: Name of the span.
            parent: Parent span or trace.

        Returns:
            Context manager for the span.

        Notes:
            Spans should be created for significant operations like
            tool execution, LLM calls, and state transitions.
        """
        ...
    
    def log_io(self, input_data: Any, output_data: Any) -> None:
        """Log input/output data for a span.

        Args:
            input_data: Input data to log.
            output_data: Output data to log.

        Notes:
            Input/output logging should respect redaction policies
            and privacy requirements.
        """
        ...
    
    def log_decision(self, decision: str, context: dict[str, Any]) -> None:
        """Log a decision point in the execution.

        Args:
            decision: Decision that was made.
            context: Context information for the decision.

        Notes:
            Decision logging helps with debugging and understanding
            the agent's decision-making process.
        """
        ...
    
    def flush(self) -> None:
        """Flush all pending trace data.

        Notes:
            This method should be called at the end of agent execution
            to ensure all trace data is persisted.
        """
        ...

