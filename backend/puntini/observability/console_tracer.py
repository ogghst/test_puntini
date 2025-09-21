"""Console tracer implementation.

This module provides a console-based implementation of the Tracer interface
for development and debugging purposes.
"""

import time
from contextlib import AbstractContextManager
from typing import Any, Dict
from ..interfaces.tracer import Tracer


class ConsoleTracer:
    """Console implementation of Tracer.
    
    This implementation logs trace and span information to the console
    for development and debugging purposes.
    """
    
    def __init__(self, config: Dict[str, Any] | None = None):
        """Initialize the console tracer.
        
        Args:
            config: Optional configuration dictionary.
        """
        self._config = config or {}
        self._indent_level = 0
        self._trace_id = None
    
    def start_trace(self, name: str, trace_id: str | None = None) -> AbstractContextManager:
        """Start a new trace for agent execution.

        Args:
            name: Name of the trace.
            trace_id: Optional trace ID (generated if not provided).

        Returns:
            Context manager for the trace.
        """
        if trace_id is None:
            trace_id = f"trace_{int(time.time())}"
        
        self._trace_id = trace_id
        print(f"🔍 Starting trace: {name} (ID: {trace_id})")
        return ConsoleContextManager(self, "trace", name)
    
    def start_span(self, name: str, parent: Any | None = None) -> AbstractContextManager:
        """Start a new span within a trace.

        Args:
            name: Name of the span.
            parent: Parent span or trace (ignored).

        Returns:
            Context manager for the span.
        """
        self._indent_level += 1
        indent = "  " * self._indent_level
        print(f"{indent}📊 Starting span: {name}")
        return ConsoleContextManager(self, "span", name)
    
    def log_io(self, input_data: Any, output_data: Any) -> None:
        """Log input/output data for a span.

        Args:
            input_data: Input data to log.
            output_data: Output data to log.
        """
        indent = "  " * (self._indent_level + 1)
        print(f"{indent}📥 Input: {str(input_data)[:100]}...")
        print(f"{indent}📤 Output: {str(output_data)[:100]}...")
    
    def log_decision(self, decision: str, context: dict[str, Any]) -> None:
        """Log a decision point in the execution.

        Args:
            decision: Decision that was made.
            context: Context information for the decision.
        """
        indent = "  " * (self._indent_level + 1)
        print(f"{indent}🤔 Decision: {decision}")
        if context:
            print(f"{indent}   Context: {str(context)[:100]}...")
    
    def flush(self) -> None:
        """Flush all pending trace data.
        
        Console tracer doesn't need to flush.
        """
        print("✅ Trace completed")


class ConsoleContextManager(AbstractContextManager):
    """Console context manager for traces and spans."""
    
    def __init__(self, tracer: ConsoleTracer, context_type: str, name: str):
        """Initialize the context manager.
        
        Args:
            tracer: Parent tracer instance.
            context_type: Type of context ("trace" or "span").
            name: Name of the context.
        """
        self._tracer = tracer
        self._context_type = context_type
        self._name = name
        self._start_time = time.time()
    
    def __enter__(self):
        """Enter the context."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context."""
        duration = time.time() - self._start_time
        indent = "  " * self._tracer._indent_level
        
        if self._context_type == "span":
            self._tracer._indent_level -= 1
        
        status = "❌" if exc_type else "✅"
        print(f"{indent}{status} {self._context_type.title()}: {self._name} ({duration:.3f}s)")
        
        if exc_type:
            print(f"{indent}   Error: {exc_val}")
    
    def log_io(self, input_data: Any, output_data: Any) -> None:
        """Log input/output data for this context.
        
        Args:
            input_data: Input data to log.
            output_data: Output data to log.
        """
        self._tracer.log_io(input_data, output_data)
    
    def log_decision(self, decision: str, context: dict[str, Any]) -> None:
        """Log a decision point in this context.
        
        Args:
            decision: Decision that was made.
            context: Context information for the decision.
        """
        self._tracer.log_decision(decision, context)