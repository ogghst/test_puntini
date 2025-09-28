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

### Backend Setup

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

## Docker

The application can be run in Docker containers. There are separate Docker images for the backend API and frontend application.

### Backend Docker Image

The backend Docker image exposes port 8025 for the web API.

#### Building the Backend Docker Image

```bash
cd backend
docker build -t puntini-backend:latest .
```

#### Running the Backend Docker Container

```bash
docker run -p 8025:8025 puntini-backend:latest
```

The API will be available at http://localhost:8025

### Frontend Docker Image

The frontend Docker image exposes port 8026 for the web application and connects to the backend API at http://localhost:8025.

#### Building the Frontend Docker Image

```bash
cd frontend
docker build -t puntini-frontend:latest .
```

#### Running the Frontend Docker Container

```bash
docker run -p 8026:8026 puntini-frontend:latest
```

The frontend will be available at http://localhost:8026

### Running Both Containers

To run both the backend and frontend containers together:

```bash
# Start the backend
docker run -d --name puntini-backend -p 8025:8025 puntini-backend:latest

# Start the frontend
docker run -d --name puntini-frontend -p 8026:8026 puntini-frontend:latest

# Access the frontend at http://localhost:8026
# The frontend will connect to the backend at http://localhost:8025
```

## GitHub Actions

The project includes GitHub Actions workflows for automated testing and building of Docker images:

### Backend Workflow

Located at `.github/workflows/backend-docker.yml`, this workflow:
- Builds the backend Docker image on pushes to main branch
- Runs tests to verify the container works correctly
- Only triggers on changes to backend files

### Frontend Workflow

Located at `.github/workflows/frontend-docker.yml`, this workflow:
- Builds the frontend Docker image on pushes to main branch
- Runs tests to verify the container works correctly
- Only triggers on changes to frontend files

There is also a `.github/workflows/docker-publish.yml` workflow that publishes the backend Docker image to Docker Hub.

All workflows use Docker Buildx for efficient building and caching.

## API Documentation

When running the server, API documentation is available at:
- Swagger UI: http://localhost:8025/docs
- ReDoc: http://localhost:8025/redoc

## License

This project is licensed under the MIT License - see the LICENSE file for details.

