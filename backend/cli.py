"""Command-line interface for the agent system.

This module provides a CLI for running the agent with various
configurations and options.
"""

import click
import sys
from pathlib import Path
from typing import Any, Dict

# Note: Path modification removed to avoid import conflicts
# The CLI should be run as a module: python -m puntini.cli

from puntini.agents.agent_factory import create_simple_agent, create_agent_with_components
from puntini.utils.settings import settings
from langfuse.langchain import CallbackHandler
from langfuse import Langfuse
from langfuse import get_client
import uuid


def print_graph_summary(graph_store):
    """Print a summary of the graph showing all nodes and edges.
    
    Args:
        graph_store: The graph store instance to query.
    """
    try:
        # Get all nodes and edges
        nodes = graph_store.get_all_nodes()
        edges = graph_store.get_all_edges()
        
        click.echo("\n" + "="*60)
        click.echo("📊 GRAPH SUMMARY")
        click.echo("="*60)
        
        # Print nodes
        click.echo(f"\n🔵 NODES ({len(nodes)} total):")
        if not nodes:
            click.echo("  No nodes found in the graph.")
        else:
            for i, node in enumerate(nodes, 1):
                click.echo(f"  {i}. [{node.label}] {node.key}")
                click.echo(f"     ID: {node.id}")
                if node.properties:
                    props_str = ", ".join([f"{k}={v}" for k, v in node.properties.items()])
                    click.echo(f"     Properties: {props_str}")
                else:
                    click.echo("     Properties: None")
        
        # Print edges
        click.echo(f"\n🔗 EDGES ({len(edges)} total):")
        if not edges:
            click.echo("  No edges found in the graph.")
        else:
            for i, edge in enumerate(edges, 1):
                click.echo(f"  {i}. ({edge.source_label}:{edge.source_key}) --[{edge.relationship_type}]--> ({edge.target_label}:{edge.target_key})")
                click.echo(f"     ID: {edge.id}")
                if edge.properties:
                    props_str = ", ".join([f"{k}={v}" for k, v in edge.properties.items()])
                    click.echo(f"     Properties: {props_str}")
                else:
                    click.echo("     Properties: None")
        
        # Print graph statistics
        click.echo(f"\n📈 STATISTICS:")
        click.echo(f"  Total Nodes: {len(nodes)}")
        click.echo(f"  Total Edges: {len(edges)}")
        
        # Group nodes by label
        label_counts = {}
        for node in nodes:
            label_counts[node.label] = label_counts.get(node.label, 0) + 1
        
        if label_counts:
            click.echo(f"  Nodes by Label:")
            for label, count in sorted(label_counts.items()):
                click.echo(f"    {label}: {count}")
        
        # Group edges by relationship type
        rel_counts = {}
        for edge in edges:
            rel_counts[edge.relationship_type] = rel_counts.get(edge.relationship_type, 0) + 1
        
        if rel_counts:
            click.echo(f"  Edges by Relationship:")
            for rel_type, count in sorted(rel_counts.items()):
                click.echo(f"    {rel_type}: {count}")
        
        click.echo("="*60)
        
    except Exception as e:
        click.echo(f"❌ Error printing graph summary: {e}")
        if hasattr(graph_store, '_nodes') and hasattr(graph_store, '_edges'):
            # Fallback: try to access internal data directly
            try:
                nodes = list(graph_store._nodes.values())
                edges = list(graph_store._edges.values())
                click.echo(f"  Fallback: Found {len(nodes)} nodes and {len(edges)} edges")
            except Exception as fallback_error:
                click.echo(f"  Fallback also failed: {fallback_error}")



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
    
    # Create agent with proper components
    from puntini.graph.graph_store_factory import create_memory_graph_store
    from puntini.context.context_manager_factory import create_simple_context_manager
    from puntini.tools.tool_setup import create_tool_registry_with_validation
    from puntini.observability.tracer_factory import create_console_tracer
    from puntini import create_agent_with_components, create_initial_state
    
    # Create all required components
    graph_store = create_memory_graph_store()
    context_manager = create_simple_context_manager()
    tool_registry = create_tool_registry_with_validation()
    tracer = create_console_tracer()
    
    # Create agent with components
    agent = create_agent_with_components(
        graph_store=graph_store,
        context_manager=context_manager,
        tool_registry=tool_registry,
        tracer=tracer
    )
    
    # Create proper initial state with all components
    initial_state = create_initial_state(
        goal=goal,
        graph_store=graph_store,
        context_manager=context_manager,
        tool_registry=tool_registry,
        tracer=tracer,
        max_retries=settings.max_retries
    )
    
    # Run the agent
    try:
        #with tracer_instance.start_trace("agent-execution") as trace:
        #    # Create config with thread_id for checkpointer
        #    import uuid
        #    thread_id = str(uuid.uuid4())
        #    from puntini.observability.langfuse_callback import LangfuseCallbackHandler
        #    langfuse_handler =  CallbackHandler()
        #    config = {"configurable": {"thread_id": thread_id}, "callbacks": [langfuse_handler]}
            
        #    result = agent.invoke(initial_state, config=config)
        #    click.echo(f"✅ Agent completed successfully!")
        #    if verbose:
        #        click.echo(f"Result: {result}")
        
        Langfuse(
            secret_key=settings.langfuse.secret_key,
            public_key=settings.langfuse.public_key,
            host=settings.langfuse.host
        )   
        langfuse = get_client()
        langfuse_handler = CallbackHandler()
        thread_id = str(uuid.uuid4())
        
        # Create LLM for the graph context
        from puntini.llm.llm_models import LLMFactory
        llm_factory = LLMFactory()
        llm = llm_factory.get_default_llm()
        
        # Pass LLM and components through context
        context = {
            "llm": llm,
            "graph_store": graph_store,
            "context_manager": context_manager,
            "tool_registry": tool_registry,
            "tracer": tracer
        }
        config = {
            "configurable": {"thread_id": thread_id}, 
            "callbacks": [langfuse_handler],
            "recursion_limit": 100  # Increase from default 25 to 100
        }
        
        result = agent.invoke(initial_state, config=config, context=context)
        click.echo(f"✅ Agent completed successfully!")
        if verbose:
            click.echo(f"Result: {result}")
        
        # Print graph summary
        print_graph_summary(graph_store)
        
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
@click.option("--create-default-users", is_flag=True, default=True, help="Create default users (admin and user)")
@click.option("--no-default-users", is_flag=True, help="Skip creating default users")
@click.option("--reset", is_flag=True, help="Reset database (WARNING: deletes all data!)")
@click.option("--health-check", is_flag=True, help="Check database health")
def init_db(create_default_users: bool, no_default_users: bool, reset: bool, health_check: bool):
    """Initialize the database with tables and default data.
    
    Args:
        create_default_users: Whether to create default users.
        no_default_users: Skip creating default users.
        reset: Reset database (WARNING: deletes all data!).
        health_check: Check database health.
    """
    import asyncio
    from puntini.database.init_db import initialize_database, reset_database, check_database_health
    
    if health_check:
        click.echo("🔍 Checking database health...")
        result = asyncio.run(check_database_health())
        if result:
            click.echo("✅ Database health check passed")
            return
        else:
            click.echo("❌ Database health check failed")
            sys.exit(1)
    
    if reset:
        if click.confirm("⚠️  This will delete ALL data in the database. Are you sure?"):
            click.echo("🔄 Resetting database...")
            asyncio.run(reset_database())
            click.echo("✅ Database reset completed")
        else:
            click.echo("❌ Database reset cancelled")
        return
    
    click.echo("🚀 Initializing database...")
    create_users = create_default_users and not no_default_users
    asyncio.run(initialize_database(create_users))
    click.echo("✅ Database initialization completed")


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
