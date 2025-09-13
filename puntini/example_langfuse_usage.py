#!/usr/bin/env python3
"""Example usage of the LangfuseTracer implementation.

This example demonstrates how to use the LangfuseTracer for observability
in the puntini agent system with settings integration.
"""

import os
from puntini.settings import Settings
from puntini.observability.tracer_factory import make_tracer, TracerConfig


def example_agent_workflow():
    """Example of how to use LangfuseTracer in an agent workflow with settings."""
    
    # Load settings from config.json
    settings = Settings("config.json")
    
    # Create tracer using settings
    tracer_cfg = TracerConfig("langfuse")
    tracer = make_tracer(tracer_cfg, settings)
    
    # Example agent execution with tracing
    with tracer.start_trace("agent-execution") as trace:
        # Log the initial goal
        tracer.log_io(
            {"goal": "Process user request", "user_id": "user_123"},
            {"status": "started"}
        )
        
        # Simulate planning phase
        with tracer.start_span("planning") as plan_span:
            tracer.log_decision("use_tool", {"tool": "graph_ops", "reason": "user wants to add node"})
            plan_span.log_io(
                {"step": "analyze_request"},
                {"plan": ["parse_goal", "select_tool", "execute_tool"]}
            )
        
        # Simulate tool execution
        with tracer.start_span("tool-execution") as tool_span:
            tracer.log_io(
                {"tool": "add_node", "params": {"label": "User", "properties": {"name": "John"}}},
                {"result": "success", "node_id": "node_123"}
            )
            tool_span.log_decision("retry_on_failure", {"attempt": 1, "max_attempts": 3})
        
        # Log final result
        tracer.log_io(
            {"status": "processing"},
            {"result": "success", "nodes_created": 1, "execution_time": "2.5s"}
        )
    
    # Flush all traces to Langfuse
    tracer.flush()
    print("✓ Agent workflow traced successfully with settings integration!")


def example_direct_configuration():
    """Example of using LangfuseTracer with direct configuration (overrides settings)."""
    from puntini.observability.langfuse_tracer import LangfuseTracer
    
    # Direct configuration (takes precedence over settings)
    config = {
        "public_key": os.getenv("LANGFUSE_PUBLIC_KEY", "your-public-key"),
        "secret_key": os.getenv("LANGFUSE_SECRET_KEY", "your-secret-key"),
        "host": os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
        "debug": True,
        "tracing_enabled": True,
        "sample_rate": 1.0
    }
    
    # Initialize tracer with direct config
    tracer = LangfuseTracer(config)
    
    with tracer.start_trace("direct-config-example") as trace:
        tracer.log_io({"method": "direct_config"}, {"status": "success"})
    
    tracer.flush()
    print("✓ Direct configuration example completed!")


if __name__ == "__main__":
    print("=== Settings Integration Example ===")
    example_agent_workflow()
    
    print("\n=== Direct Configuration Example ===")
    example_direct_configuration()
