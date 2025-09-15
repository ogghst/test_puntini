"""Langfuse callback handler for LangChain integration.

This module provides a LangChain callback handler that integrates with
Langfuse for automatic tracing of LLM calls and tool executions.
"""

from typing import Any, Dict, List, Optional, Union
from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_core.outputs import LLMResult
from langchain_core.messages import BaseMessage
from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.tools import BaseTool

from .langfuse_tracer import LangfuseTracer


class LangfuseCallbackHandler(BaseCallbackHandler):
    """LangChain callback handler for Langfuse tracing.
    
    This handler automatically traces LLM calls, tool executions, and other
    LangChain operations using Langfuse for observability.
    """
    
    def __init__(self, tracer: LangfuseTracer, trace_id: Optional[str] = None):
        """Initialize the Langfuse callback handler.
        
        Args:
            tracer: Langfuse tracer instance for logging.
            trace_id: Optional trace ID to use for all operations.
        """
        super().__init__()
        self.tracer = tracer
        self.trace_id = trace_id
        self._current_span = None
        self._span_stack = []
    
    def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        **kwargs: Any
    ) -> None:
        """Called when an LLM starts running.
        
        Args:
            serialized: Serialized LLM configuration.
            prompts: List of prompts sent to the LLM.
            **kwargs: Additional keyword arguments.
        """
        # Extract model information
        model_name = serialized.get("id", ["unknown"])[-1] if serialized.get("id") else "unknown"
        
        # Create span for LLM call
        span_name = f"llm_call_{model_name}"
        self._current_span = self.tracer.start_span(span_name, parent=self._current_span)
        self._span_stack.append(self._current_span)
        
        # Log input data
        self._current_span.__enter__()
        # Note: log_io is called on the span object, not the tracer
        # The span object will handle the logging internally
    
    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """Called when an LLM ends running.
        
        Args:
            response: The LLM response.
            **kwargs: Additional keyword arguments.
        """
        if self._current_span:
            # Exit the span
            self._current_span.__exit__(None, None, None)
            
            # Pop from stack
            if self._span_stack:
                self._span_stack.pop()
                self._current_span = self._span_stack[-1] if self._span_stack else None
    
    def on_llm_error(self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any) -> None:
        """Called when an LLM encounters an error.
        
        Args:
            error: The error that occurred.
            **kwargs: Additional keyword arguments.
        """
        if self._current_span:
            # Exit the span with error
            self._current_span.__exit__(type(error), error, None)
            
            # Pop from stack
            if self._span_stack:
                self._span_stack.pop()
                self._current_span = self._span_stack[-1] if self._span_stack else None
    
    def on_chain_start(
        self,
        serialized: Dict[str, Any],
        inputs: Dict[str, Any],
        **kwargs: Any
    ) -> None:
        """Called when a chain starts running.
        
        Args:
            serialized: Serialized chain configuration.
            inputs: Inputs to the chain.
            **kwargs: Additional keyword arguments.
        """
        # Extract chain name
        chain_name = serialized.get("id", ["unknown"])[-1] if serialized.get("id") else "unknown"
        
        # Create span for chain
        span_name = f"chain_{chain_name}"
        self._current_span = self.tracer.start_span(span_name, parent=self._current_span)
        self._span_stack.append(self._current_span)
        
        # Log input data
        self._current_span.__enter__()
        # Note: log_io is called on the span object, not the tracer
        # The span object will handle the logging internally
    
    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None:
        """Called when a chain ends running.
        
        Args:
            outputs: Outputs from the chain.
            **kwargs: Additional keyword arguments.
        """
        if self._current_span:
            # Exit the span
            self._current_span.__exit__(None, None, None)
            
            # Pop from stack
            if self._span_stack:
                self._span_stack.pop()
                self._current_span = self._span_stack[-1] if self._span_stack else None
    
    def on_chain_error(self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any) -> None:
        """Called when a chain encounters an error.
        
        Args:
            error: The error that occurred.
            **kwargs: Additional keyword arguments.
        """
        if self._current_span:
            # Exit the span with error
            self._current_span.__exit__(type(error), error, None)
            
            # Pop from stack
            if self._span_stack:
                self._span_stack.pop()
                self._current_span = self._span_stack[-1] if self._span_stack else None
    
    def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        **kwargs: Any
    ) -> None:
        """Called when a tool starts running.
        
        Args:
            serialized: Serialized tool configuration.
            input_str: Input string to the tool.
            **kwargs: Additional keyword arguments.
        """
        # Extract tool name
        tool_name = serialized.get("name", "unknown")
        
        # Create span for tool
        span_name = f"tool_{tool_name}"
        self._current_span = self.tracer.start_span(span_name, parent=self._current_span)
        self._span_stack.append(self._current_span)
        
        # Log input data
        self._current_span.__enter__()
        # Note: log_io is called on the span object, not the tracer
        # The span object will handle the logging internally
    
    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        """Called when a tool ends running.
        
        Args:
            output: Output from the tool.
            **kwargs: Additional keyword arguments.
        """
        if self._current_span:
            # Exit the span
            self._current_span.__exit__(None, None, None)
            
            # Pop from stack
            if self._span_stack:
                self._span_stack.pop()
                self._current_span = self._span_stack[-1] if self._span_stack else None
    
    def on_tool_error(self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any) -> None:
        """Called when a tool encounters an error.
        
        Args:
            error: The error that occurred.
            **kwargs: Additional keyword arguments.
        """
        if self._current_span:
            # Exit the span with error
            self._current_span.__exit__(type(error), error, None)
            
            # Pop from stack
            if self._span_stack:
                self._span_stack.pop()
                self._current_span = self._span_stack[-1] if self._span_stack else None
    
    def on_agent_action(self, action: AgentAction, **kwargs: Any) -> None:
        """Called when an agent takes an action.
        
        Args:
            action: The action taken by the agent.
            **kwargs: Additional keyword arguments.
        """
        # Note: Agent actions are logged at the span level
        pass
    
    def on_agent_finish(self, finish: AgentFinish, **kwargs: Any) -> None:
        """Called when an agent finishes.
        
        Args:
            finish: The finish result from the agent.
            **kwargs: Additional keyword arguments.
        """
        # Note: Agent finish is logged at the span level
        pass
    
    def on_text(self, text: str, **kwargs: Any) -> None:
        """Called when text is generated.
        
        Args:
            text: The generated text.
            **kwargs: Additional keyword arguments.
        """
        # Note: Text generation is logged at the span level
        pass
    
    def flush(self) -> None:
        """Flush any pending traces to Langfuse."""
        if hasattr(self.tracer, 'flush'):
            self.tracer.flush()
