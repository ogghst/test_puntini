# Puntini Agent

A controllable, observable multi-tool agent for graph manipulation using LangGraph + LangChain, with progressive context disclosure, intelligent escalation, strict contracts, and production-grade instrumentation via Langfuse.

For detailed architectural information, see [AGENTS.md](AGENTS.md).

## Features

- **Stateful Agent**: Translates natural language into safe, idempotent graph operations
- **LangGraph Orchestration**: State machine with conditional edges, Command, checkpointer, and interrupts
- **Progressive Context Disclosure**: Gradual context increase across retry attempts
- **Observability**: Langfuse traces/spans with comprehensive monitoring
- **Graph Database Support**: Neo4j with MERGE-based idempotent writes and in-memory graph store
- **Tool Ecosystem**: Structured tool calling with Pydantic schemas
- **Multi-LLM Support**: OpenAI, Anthropic, Ollama, DeepSeek and other providers
- **Web API**: FastAPI-based REST and WebSocket interface for remote interaction
- **Configuration Management**: JSON-based configuration with multiple environments

## Quick Start

### Installation

```bash
cd backend
pip install -r requirements.txt
```

### Basic Usage

```python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from puntini import create_simple_agent, create_console_tracer
from puntini.utils.settings import settings

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
from langfuse.langchain import CallbackHandler
from langfuse import Langfuse
from langfuse import get_client
import uuid

# Setup tracing
langfuse_handler = CallbackHandler()
thread_id = str(uuid.uuid4())
config = {"configurable": {"thread_id": thread_id}, "callbacks": [langfuse_handler]}

# Create LLM for the graph context
from puntini.llm.llm_models import LLMFactory
llm_factory = LLMFactory()
llm = llm_factory.get_default_llm()

# Pass LLM through context
context = {"llm": llm}

# Run the agent
result = agent.invoke(initial_state, config=config, context=context)
print(f"Result: {result}")
```

### CLI Usage

```bash
cd backend

# Run with a goal
python -m puntini.cli run --goal "Create a node called 'Test'"

# Show configuration
python -m puntini.cli config-show

# Run tests
python -m puntini.cli test

# Generate example configuration
python -m puntini.cli example
```

### Web API Usage

```bash
cd backend

# Start the server
python run_server.py

# Or use the CLI
python -m puntini.cli run-server
```

## Configuration

Create a `config.json` file with your configuration (see `config.json.example` for a full example):

```json
{
  "langfuse": {
    "secret_key": "your_secret_key_here",
    "public_key": "your_public_key_here",
    "host": "https://cloud.langfuse.com"
  },
  "llm": {
    "default_llm": "openai-gpt4",
    "providers": [
      {
        "name": "openai-gpt4",
        "type": "openai",
        "api_key": "your_openai_api_key_here",
        "model_name": "gpt-4",
        "temperature": 0.0,
        "enabled": true
      }
    ]
  },
  "neo4j": {
    "uri": "bolt://localhost:7687",
    "username": "neo4j",
    "password": "password"
  },
  "agent": {
    "max_retries": 3,
    "checkpointer_type": "memory",
    "tracer_type": "console"
  }
}
```

## Architecture

The agent follows a modular architecture with clear separation of concerns:

- **Interfaces**: Protocol definitions for all components (in `puntini/interfaces/`)
- **Models**: Base entities with UUIDv4 and timestamp management (in `puntini/models/`)
- **Factories**: Configuration-driven component creation (in `puntini/*/factory.py`)
- **Orchestration**: LangGraph state machine with nodes and edges (in `puntini/orchestration/`)
- **Nodes**: Implementation of each step in the agent workflow (in `puntini/nodes/`)
- **Tools**: Graph operations and Cypher QA capabilities (in `puntini/tools/`)
- **Observability**: Tracing and monitoring with Langfuse (in `puntini/observability/`)
- **API**: FastAPI-based REST and WebSocket interface (in `puntini/api/`)

## State Machine

The agent uses a LangGraph state machine with the following nodes:

1. **ParseGoal**: Extract goal, constraints, and domain hints from natural language
2. **PlanStep**: Propose next micro-step and tool signature
3. **RouteTool**: Select tool or branch for execution
4. **CallTool**: Execute tool with validated inputs
5. **Evaluate**: Decide advance, retry, or diagnose (returns Command for update+goto)
6. **Diagnose**: Classify failures and choose remediation
7. **Escalate**: Interrupt for human input with checkpointing
8. **Answer**: Synthesize final answer and close cleanly

For a visual representation of the graph flow, see [GRAPH.md](GRAPH.md).

## Development

### Running Tests

```bash
cd backend
python -m puntini.cli test
```

### Code Quality

```bash
cd backend

# Format code
black puntini/

# Sort imports
isort puntini/

# Type checking
mypy puntini/
```

## API Documentation

When running the server, API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## License

This project is licensed under the MIT License - see the LICENSE file for details.

