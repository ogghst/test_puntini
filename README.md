# Puntini

![puntini](docs/puntini.png)

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

### Option 1: Docker (Recommended)

The easiest way to run the application is with Docker:

```bash
# Full stack with all services (Neo4j, Ollama, Langfuse)
docker-compose up -d

# Minimal setup (just frontend and backend in one container)
docker-compose -f docker-compose-minimal.yml up -d
```

**Access the application:**
- Frontend: http://localhost:8025
- Backend API: http://localhost:8026
- API Docs: http://localhost:8026/docs

For detailed Docker setup instructions, see [DOCKER_SETUP.md](DOCKER_SETUP.md).

### Option 2: Local Installation

1.  **Navigate to the backend directory:**
    ```bash
    cd apps/backend
    ```
2.  **Create a virtual environment and install the dependencies:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt

    ```
3.  **Run the development server:**
    ```bash
    python run_server.py
    ```

### Frontend Setup

1.  **Navigate to the frontend directory:**
    ```bash
    cd apps/frontend
    ```
2.  **Install the dependencies:**
    ```bash
    npm install
    ```
3.  **Run the development server:**
    ```bash
    npm run dev
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

## Docker Deployment

The application provides three Docker images for flexible deployment:

### 1. Backend Image (`backend/Dockerfile`)
- Standalone Python backend service
- Port: 8026
- Config: `backend/config.docker.json`

### 2. Frontend Image (`frontend/Dockerfile`)
- Standalone React frontend service
- Port: 8025
- Config: `frontend/.env.docker`

### 3. Combined Image (`Dockerfile.combined`)
- Single container with both services
- Ports: 8025 (frontend), 8026 (backend)
- Uses same config files as standalone images

**Build individual images:**
```bash
# Backend
docker build -t puntini-backend -f backend/Dockerfile backend/

# Frontend
docker build -t puntini-frontend -f frontend/Dockerfile .

# Combined
docker build -t puntini-combined -f Dockerfile.combined .
```

For more details, see [DOCKER_SETUP.md](DOCKER_SETUP.md).

## API Documentation

When running the server, API documentation is available at:
- Docker: http://localhost:8026/docs (Swagger UI) and http://localhost:8026/redoc (ReDoc)
- Local: http://localhost:8000/docs (Swagger UI) and http://localhost:8000/redoc (ReDoc)

## License

This project is licensed under the MIT License - see the LICENSE file for details.

