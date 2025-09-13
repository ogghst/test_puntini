"""Command-line interface for the agent system.

This module provides a CLI for running the agent with various
configurations and options.
"""

import click
import sys
from pathlib import Path
from typing import Any, Dict

# Add the project root to the Python path for direct execution
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from puntini.agents.agent_factory import create_simple_agent, create_agent_with_components
from puntini.settings import settings


@click.group()
def cli():
    """Puntini Agent - A controllable, observable multi-tool agent for graph manipulation."""
    pass


@cli.command()
@click.option("--goal", "-g", required=True, help="Goal for the agent to accomplish")
@click.option("--config", "-c", help="Path to configuration file")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--tracer", "-t", default="console", help="Tracer type (console, noop, langfuse)")
def run(goal: str, config: str | None, verbose: bool, tracer: str):
    """Run the agent with a specific goal.
    
    Args:
        goal: The goal for the agent to accomplish.
        config: Optional path to configuration file.
        verbose: Enable verbose output.
        tracer: Type of tracer to use.
    """
    click.echo(f"🎯 Running agent with goal: {goal}")
    
    # Create agent
    if tracer == "noop":
        from puntini.observability.tracer_factory import create_noop_tracer
        tracer_instance = create_noop_tracer()
    elif tracer == "console":
        from puntini.observability.tracer_factory import create_console_tracer
        tracer_instance = create_console_tracer()
    elif tracer == "langfuse":
        from puntini.observability.tracer_factory import create_langfuse_tracer
        tracer_instance = create_langfuse_tracer()
    else:
        click.echo(f"❌ Unsupported tracer type: {tracer}")
        return
    
    # Create simple agent for now
    agent = create_simple_agent()
    
    # Prepare initial state
    initial_state = {
        "goal": goal,
        "plan": [],
        "progress": [],
        "failures": [],
        "retry_count": 0,
        "max_retries": settings.max_retries,
        "messages": [],
        "current_step": "parse_goal",
        "current_attempt": 1,
        "artifacts": [],
        "result": {},
        "_tool_signature": {},
        "_error_context": {},
        "_escalation_context": {}
    }
    
    # Run the agent
    try:
        with tracer_instance.start_trace("agent-execution") as trace:
            # Create config with thread_id for checkpointer
            import uuid
            thread_id = str(uuid.uuid4())
            config = {"configurable": {"thread_id": thread_id}}
            
            result = agent.invoke(initial_state, config=config)
            click.echo(f"✅ Agent completed successfully!")
            if verbose:
                click.echo(f"Result: {result}")
    except Exception as e:
        click.echo(f"❌ Agent failed: {e}")
        if verbose:
            import traceback
            traceback.print_exc()


@cli.command()
@click.option("--config", "-c", help="Path to configuration file")
def config_show(config: str | None):
    """Show current configuration.
    
    Args:
        config: Optional path to configuration file.
    """
    click.echo("📋 Current Configuration:")
    click.echo(f"  Model: {settings.model_name}")
    click.echo(f"  Max Retries: {settings.max_retries}")
    click.echo(f"  Checkpointer: {settings.checkpointer_type}")
    click.echo(f"  Tracer: {settings.tracer_type}")
    click.echo(f"  Debug: {settings.debug}")


@cli.command()
def test():
    """Run basic tests to verify the system is working."""
    click.echo("🧪 Running basic tests...")
    
    try:
        # Test agent creation
        agent = create_simple_agent()
        click.echo("✅ Agent creation: PASSED")
        
        # Test tracer creation
        from puntini.observability.tracer_factory import create_langfuse_tracer
        tracer = create_langfuse_tracer()
        click.echo("✅ Tracer creation: PASSED")
        
        # Test graph store creation
        from puntini.graph.graph_store_factory import create_memory_graph_store
        graph_store = create_memory_graph_store()
        click.echo("✅ Graph store creation: PASSED")
        
        click.echo("🎉 All tests passed!")
        
    except Exception as e:
        click.echo(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


@cli.command()
@click.option("--output", "-o", help="Output file for the example")
def example(output: str | None):
    """Generate an example configuration file.
    
    Args:
        output: Output file path (default: .env.example).
    """
    if output is None:
        output = ".env.example"
    
    example_content = """# Puntini Agent Configuration

# Langfuse Configuration (for observability)
LANGFUSE_PUBLIC_KEY=your_public_key_here
LANGFUSE_SECRET_KEY=your_secret_key_here
LANGFUSE_HOST=https://cloud.langfuse.com

# LLM Configuration
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
MODEL_NAME=gpt-4
MODEL_TEMPERATURE=0.0

# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password

# Agent Configuration
MAX_RETRIES=3
CHECKPOINTER_TYPE=memory
TRACER_TYPE=console

# Development Settings
DEBUG=false
LOG_LEVEL=INFO
"""
    
    with open(output, "w") as f:
        f.write(example_content)
    
    click.echo(f"📝 Example configuration written to {output}")


if __name__ == "__main__":
    cli()
