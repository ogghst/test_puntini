"""Langfuse tracer implementation.

This module provides a Langfuse-based implementation of the Tracer interface
for production observability and monitoring.
"""

import time
from contextlib import AbstractContextManager
from typing import Any, Dict, Optional
from ..interfaces.tracer import Tracer
from ..settings import Settings

try:
    from langfuse import get_client, Langfuse
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False
    # Create a mock Langfuse class for type hints when not available
    class Langfuse:
        pass


class LangfuseTracer:
    """Langfuse implementation of Tracer.
    
    This implementation integrates with Langfuse for production
    observability and monitoring using the Langfuse Python SDK v3.
    """
    
    def __init__(self, config: Dict[str, Any] | None = None, settings: Settings | None = None):
        """Initialize the Langfuse tracer.
        
        Args:
            config: Optional configuration dictionary containing Langfuse settings.
                   If provided, takes precedence over settings.
            settings: Optional Settings instance. If not provided, uses global settings.
        """
        if not LANGFUSE_AVAILABLE:
            raise ImportError(
                "Langfuse is not installed. Install it with: pip install langfuse"
            )
        
        self._settings = settings or Settings()
        self._config = config or {}
        self._langfuse_client: Optional[Langfuse] = None
        self._trace_id: Optional[str] = None
        self._current_span: Optional[Any] = None
        self._initialized = False
        
        self._ensure_initialized()
    
    def _ensure_initialized(self) -> None:
        """Ensure the Langfuse client is initialized."""
        if not self._initialized:
            try:
                # Get configuration from settings or config
                if self._config:
                    # Use provided config (takes precedence)
                    langfuse_config = self._config
                else:
                    # Use settings configuration
                    langfuse_config = self._settings.get_tracer_config()["langfuse"]
                
                # Initialize Langfuse client with configuration
                if langfuse_config.get("public_key") and langfuse_config.get("secret_key"):
                    print(f"Initializing Langfuse client with host: {langfuse_config.get('host')}")
                    self._langfuse_client = Langfuse(
                        public_key=langfuse_config.get("public_key"),
                        secret_key=langfuse_config.get("secret_key"),
                        host=langfuse_config.get("host", "https://cloud.langfuse.com"),
                        debug=langfuse_config.get("debug", False),
                        tracing_enabled=langfuse_config.get("tracing_enabled", True),
                        sample_rate=langfuse_config.get("sample_rate", 1.0)
                    )
                else:
                    # Use environment variables for configuration
                    print("Using environment variables for Langfuse configuration")
                    self._langfuse_client = get_client()
                
                self._initialized = True
                print("Langfuse client initialized successfully")
            except Exception as e:
                print(f"Failed to initialize Langfuse client: {e}")
                raise RuntimeError(f"Failed to initialize Langfuse client: {e}") from e
    
    def start_trace(self, name: str, trace_id: str | None = None) -> AbstractContextManager:
        """Start a new trace for agent execution.

        Args:
            name: Name of the trace.
            trace_id: Optional trace ID (generated if not provided).
                     Must be 32 lowercase hex characters if provided.

        Returns:
            Context manager for the trace.
        """
        self._ensure_initialized()
        
        if trace_id is None:
            # Generate a deterministic trace ID using Langfuse's method
            trace_id = Langfuse.create_trace_id(seed=f"{name}_{int(time.time())}")
        else:
            # Validate trace_id format
            if not (isinstance(trace_id, str) and len(trace_id) == 32 and all(c in '0123456789abcdef' for c in trace_id)):
                # Generate a proper trace ID from the provided one
                trace_id = Langfuse.create_trace_id(seed=trace_id)
        
        self._trace_id = trace_id
        
        return LangfuseContextManager(self, "trace", name, trace_id)
    
    def start_span(self, name: str, parent: Any | None = None) -> AbstractContextManager:
        """Start a new span within a trace.

        Args:
            name: Name of the span.
            parent: Parent span or trace.

        Returns:
            Context manager for the span.
        """
        self._ensure_initialized()
        
        return LangfuseContextManager(self, "span", name, parent)
    
    def log_io(self, input_data: Any, output_data: Any) -> None:
        """Log input/output data for a span.

        Args:
            input_data: Input data to log.
            output_data: Output data to log.
        """
        self._ensure_initialized()
        
        if self._current_span:
            try:
                self._langfuse_client.update_current_span(
                    input=input_data,
                    output=output_data
                )
            except Exception as e:
                print(f"Warning: Failed to log I/O data: {e}")
                # Don't raise the error, just log it
    
    def log_decision(self, decision: str, context: dict[str, Any]) -> None:
        """Log a decision point in the execution.

        Args:
            decision: Decision that was made.
            context: Context information for the decision.
        """
        self._ensure_initialized()
        
        if self._current_span:
            try:
                self._langfuse_client.update_current_span(
                    metadata={
                        "decision": decision,
                        "decision_context": context
                    }
                )
            except Exception as e:
                print(f"Warning: Failed to log decision: {e}")
                # Don't raise the error, just log it
    
    def flush(self) -> None:
        """Flush all pending trace data.
        
        This method ensures all trace data is sent to Langfuse.
        """
        self._ensure_initialized()
        
        if self._langfuse_client:
            self._langfuse_client.flush()
    
    def _get_trace_metadata(self) -> Dict[str, Any]:
        """Get trace metadata from settings.
        
        Returns:
            Dictionary with trace metadata from settings.
        """
        langfuse_config = self._settings.get_tracer_config()["langfuse"]
        metadata = {}
        
        # Add supported trace attributes
        if langfuse_config.get("session_id"):
            metadata["session_id"] = langfuse_config["session_id"]
        if langfuse_config.get("user_id"):
            metadata["user_id"] = langfuse_config["user_id"]
        
        # Add environment and release as metadata
        trace_metadata = {}
        if langfuse_config.get("environment"):
            trace_metadata["environment"] = langfuse_config["environment"]
        if langfuse_config.get("release"):
            trace_metadata["release"] = langfuse_config["release"]
        
        if trace_metadata:
            metadata["metadata"] = trace_metadata
        
        return metadata


class LangfuseContextManager(AbstractContextManager):
    """Langfuse context manager for traces and spans."""
    
    def __init__(self, tracer: LangfuseTracer, context_type: str, name: str, parent: Any | None = None):
        """Initialize the context manager.
        
        Args:
            tracer: Parent tracer instance.
            context_type: Type of context ("trace" or "span").
            name: Name of the context.
            parent: Parent span or trace (for spans) or trace_id (for traces).
        """
        self._tracer = tracer
        self._context_type = context_type
        self._name = name
        self._parent = parent
        self._start_time = time.time()
        self._context = None
        self._trace_id = None
        self._span = None
    
    def __enter__(self):
        """Enter the context."""
        if self._context_type == "trace":
            # Create a trace using start_as_current_span
            self._context = self._tracer._langfuse_client.start_as_current_span(
                name=self._name,
                trace_context={"trace_id": self._parent} if self._parent else None
            )
            self._trace_id = self._parent
            
            # Apply trace metadata from settings
            trace_metadata = self._tracer._get_trace_metadata()
            if trace_metadata:
                self._tracer._langfuse_client.update_current_trace(**trace_metadata)
                
        elif self._context_type == "span":
            # Create a span using start_as_current_span
            self._context = self._tracer._langfuse_client.start_as_current_span(
                name=self._name
            )
            self._trace_id = self._tracer._trace_id
        
        # Enter the context manager and get the span object
        self._span = self._context.__enter__()
        
        # Set the current span in the tracer for logging
        self._tracer._current_span = self._span
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context."""
        duration = time.time() - self._start_time
        
        if self._context and self._span:
            # Update the span with duration and status
            metadata = {"duration_seconds": duration}
            if exc_type:
                metadata["status"] = "error"
                metadata["error_type"] = exc_type.__name__
                metadata["error_message"] = str(exc_val)
            else:
                metadata["status"] = "success"
            
            # Update the current span with metadata
            self._tracer._langfuse_client.update_current_span(metadata=metadata)
            
            # Exit the context manager
            self._context.__exit__(exc_type, exc_val, exc_tb)
        
        # Clear the current span from the tracer
        self._tracer._current_span = None
    
    def log_io(self, input_data: Any, output_data: Any) -> None:
        """Log input/output data for this context.
        
        Args:
            input_data: Input data to log.
            output_data: Output data to log.
        """
        if self._span:
            self._tracer._langfuse_client.update_current_span(
                input=input_data,
                output=output_data
            )
    
    def log_decision(self, decision: str, context: dict[str, Any]) -> None:
        """Log a decision point in this context.
        
        Args:
            decision: Decision that was made.
            context: Context information for the decision.
        """
        if self._span:
            self._tracer._langfuse_client.update_current_span(
                metadata={
                    "decision": decision,
                    "decision_context": context
                }
            )