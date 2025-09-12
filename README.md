# Puntini Agent

A controllable, observable multi-tool agent for graph manipulation using LangGraph + LangChain, with progressive context disclosure, intelligent escalation, strict contracts, and production-grade instrumentation via Langfuse.

## Features

- **Stateful Agent**: Translates natural language into safe, idempotent graph operations
- **LangGraph Orchestration**: State machine with conditional edges, Command, checkpointer, and interrupts
- **Progressive Context Disclosure**: Gradual context increase across retry attempts
- **Observability**: Langfuse traces/spans with comprehensive monitoring
- **Graph Database Support**: Neo4j with MERGE-based idempotent writes
- **Tool Ecosystem**: Structured tool calling with Pydantic schemas

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Basic Usage

```python
from puntini import create_simple_agent, create_console_tracer

# Create agent and tracer
agent = create_simple_agent()
tracer = create_console_tracer()

# Define a goal
goal = "Create a node called 'Example' with type 'demo'"

# Prepare initial state
initial_state = {
    "goal": goal,
    "plan": [],
    "progress": [],
    "failures": [],
    "retry_count": 0,
    "max_retries": 3,
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
with tracer.start_trace("agent-execution") as trace:
    result = agent.invoke(initial_state)
    print(f"Result: {result}")
```

### CLI Usage

```bash
# Run with a goal
python -m puntini.cli run --goal "Create a node called 'Test'"

# Show configuration
python -m puntini.cli config-show

# Run tests
python -m puntini.cli test

# Generate example configuration
python -m puntini.cli example
```

## Configuration

Create a `.env` file with your configuration:

```env
# Langfuse Configuration (for observability)
LANGFUSE_PUBLIC_KEY=your_public_key_here
LANGFUSE_SECRET_KEY=your_secret_key_here
LANGFUSE_HOST=https://cloud.langfuse.com

# LLM Configuration
OPENAI_API_KEY=your_openai_api_key_here
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
```

## Architecture

The agent follows a modular architecture with clear separation of concerns:

- **Interfaces**: Protocol definitions for all components
- **Models**: Base entities with UUIDv4 and timestamp management
- **Factories**: Configuration-driven component creation
- **Orchestration**: LangGraph state machine with nodes and edges
- **Tools**: Graph operations and Cypher QA capabilities
- **Observability**: Tracing and monitoring with Langfuse

## State Machine

The agent uses a LangGraph state machine with the following nodes:

1. **ParseGoal**: Extract goal, constraints, and domain hints
2. **PlanStep**: Propose next micro-step and tool signature
3. **RouteTool**: Select tool or branch for execution
4. **CallTool**: Execute tool with validated inputs
5. **Evaluate**: Decide advance, retry, or diagnose
6. **Diagnose**: Classify failures and choose remediation
7. **Escalate**: Interrupt for human input with checkpointing
8. **Answer**: Synthesize final answer and close cleanly

## Development

### Running Tests

```bash
python -m puntini.cli test
```

### Code Quality

```bash
# Format code
black puntini/

# Sort imports
isort puntini/

# Type checking
mypy puntini/
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

