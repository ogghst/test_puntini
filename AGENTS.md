# AGENTS.md

Purpose: Define a controllable, observable multi‑tool agent for graph manipulation using LangGraph + LangChain, with progressive context disclosure, intelligent escalation, strict contracts, and production‑grade instrumentation via Langfuse.

## Objectives

- Build a stateful agent that translates natural language into safe, idempotent graph operations and graph‑aware answers.
- Keep orchestration outside the LLM via a state graph and typed tools, enabling determinism, recoverability, and auditing.
- Add first‑class observability with Langfuse traces/spans, and enforce high‑quality docstrings across the codebase.


## Delivery Order (Scaffold First)

1) Interfaces only (no concrete logic): GraphStore, ContextManager, ToolRegistry, Planner, Executor, Evaluator, ErrorClassifier, EscalationHandler, Tracer.
2) Factories for each interface to instantiate concrete implementations from config, with test doubles for unit tests.
3) Base data models with a common code‑controlled UUIDv4 id and timestamps; no LLM‑generated identifiers.
4) LangGraph skeleton (nodes/edges) assembled around the interfaces; only then add concrete implementations (Neo4j, Langfuse).

## Tech Stack

- Orchestration: LangGraph (state machine, conditional edges, Command, checkpointer, interrupts).
- LLM \& Tools: LangChain (structured outputs, tool calling).
- Graph DB: Neo4j (MERGE‑based idempotent writes), optional GraphCypher QA.
- Observability: Langfuse (traces, spans, prompt management, evaluations).


## LLM Configuration

The agent supports multiple LLM providers (e.g., OpenAI, Anthropic, Ollama). The configuration is managed through `puntini/settings.py` and can be customized in `config.json`.

- **LLMConfig**: The main configuration object for LLMs. It defines a default LLM and holds a list of provider configurations.
- **LLMProviderConfig**: Defines the settings for a single LLM provider, including `name`, `type`, `api_key`, `model_name`, `temperature`, etc.

This setup allows for easy switching between different models and providers.

## Server Configuration

The FastAPI server configuration is managed through the settings system, allowing for flexible deployment configurations.

- **ServerConfig**: Defines server settings including host, port, reload mode, workers, and API documentation URLs.
- **Configuration Options**:
  - `host`: Server host address (default: "127.0.0.1")
  - `port`: Server port number (default: 8000)
  - `reload`: Auto-reload on code changes (default: False)
  - `workers`: Number of worker processes (default: 1)
  - `access_log`: Enable access logging (default: True)
  - `log_level`: Server log level (default: "info")
  - `root_path`: Root path for reverse proxy setups (default: "")
  - `openapi_url`: OpenAPI schema URL (default: "/openapi.json")
  - `docs_url`: API documentation URL (default: "/docs")
  - `redoc_url`: ReDoc documentation URL (default: "/redoc")

The server can be started using multiple methods:
1. Direct execution: `python puntini/api/app.py`
2. Using the example script: `python run_server.py`
3. Programmatically: `run_server(settings)`


## Logging Configuration

The system includes a configurable logging module found in `puntini/logging/`.

- **LoggingConfig**: A dataclass in `puntini/settings.py` that defines logging behavior.
- **Settings**: It includes `log_level`, `console_logging`, log file path, and rotation policies (`max_bytes`, `backup_count`).
- **Custom Formatters**: The module includes custom formatters for rich logging output.


## State Graph: Nodes and Responsibilities

- ParseGoal: Extract goal, constraints, domain hints as structured data.
- PlanStep: Propose the next micro‑step and the candidate tool signature.
- RouteTool: Select tool or branch to ask/diagnose paths.
- CallTool: Execute tool with validated inputs; normalize human‑readable errors.
- Evaluate: Decide advance, retry, or diagnose (returns Command for update+goto).
- Diagnose: Classify failure (identical/random/systematic) and choose remediation.
- Escalate: Interrupt for human input; checkpoint and deterministic resume.
- Answer: Synthesize final answer/patch summary; close cleanly.

Snippet (explicit routing via Command):

```python
def evaluate(state):
    goto = decide_next(state)  # "PlanStep" | "Diagnose" | "Answer"
    return Command(update={"progress": state["progress"]}, goto=goto)
```


## State Schema (typed and minimized)

- Fields: goal, plan, progress, failures, messages, artifacts, private channels for inter‑node data.
- Reducers prevent unbounded growth; state is the single source of truth for control.

Snippet (minimal shape):

```python
class State(TypedDict):
    goal: str
    plan: list[str]
    progress: list[str]
    failures: list[dict]
    messages: list[Any]
```


## Progressive Context Disclosure

- Attempt 1: Pass only the current task and the minimal tool signature hints.
- Attempt 2: Add the latest structured error and just‑enough payload to disambiguate.
- Attempt 3: Add selected history and a concise plan recap; possibly tighten decoding.
- Final: Escalate with a clear summary and options; resume from the same node after input.


## Instrumentation with Langfuse

- Trace each run of the state graph; create one root trace per agent session.
- Wrap sub‑agents and tool calls in child spans; propagate a stable trace_id across nested executions.
- Attach LangChain callback handler to the compiled graph so LLM/tool calls are auto‑traced.
- Record inputs/outputs and key decision points (routing, retries, escalations); flush at shutdown.
- Tag traces with model version, config hash, commit SHA, and dataset item (if evaluating).

Snippets (conceptual):

```python
# Root trace
with tracer.start_trace(name="graph-agent", trace_id=make_trace_id()) as root:
    result = graph.invoke(input=state, config={"callbacks": [langfuse_handler]})
    root.log_io(input=redact(state), output=redact(result))

# Sub-span around a tool call
with tracer.start_span(name="tool:add_edge", parent=root) as span:
    out = tool.execute(args)
    span.log_io(input=args, output=summarize(out))
```

Environment variables to define: LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST, plus model and DB credentials.

## Enforce Proper Docstrings

- Apply comprehensive docstrings on all public modules, classes, functions, and methods.
- Use Google‑style or NumPy‑style consistently; include type hints, Args, Returns, Raises, Examples, Notes, and side‑effects.
- Document preconditions, postconditions, invariants, concurrency/thread‑safety, and idempotency.
- Include clear “Warnings” where partial failures or retries can occur.

Example (Google‑style):

```python
def upsert_node(spec: NodeSpec) -> Node:
    """Create or update a node using a natural key and idempotent semantics.

    Args:
        spec: Node specification including label, key, and properties.

    Returns:
        The persisted Node with server-assigned fields populated.

    Raises:
        ConstraintViolationError: If uniqueness constraints are violated.
        ValidationError: If the input spec is not valid.

    Notes:
        Uses MERGE under the hood to guarantee idempotence.
    """
```


## Interfaces First (no concrete logic)

Define minimal, testable contracts. Do not implement concrete backends in this phase.

- GraphStore
    - Methods: upsert_node, upsert_edge, update_props, delete_node, delete_edge, run_cypher, get_subgraph.
    - Guarantees: idempotence (MERGE), transactional writes, typed errors, redaction policy.

```python
class GraphStore(Protocol):
    def upsert_node(self, spec: NodeSpec) -> Node: ...
    def upsert_edge(self, spec: EdgeSpec) -> Edge: ...
    def update_props(self, target: MatchSpec, props: dict) -> None: ...
    def delete_node(self, match: MatchSpec) -> None: ...
    def delete_edge(self, match: MatchSpec) -> None: ...
    def run_cypher(self, query: str, params: dict | None = None) -> Any: ...
```

- ContextManager
    - Methods: prepare_minimal_context, add_error_context, add_historical_context, record_failure, advance_step, is_complete.

```python
class ContextManager(Protocol):
    def prepare_minimal_context(self, state: State) -> ModelInput: ...
    def add_error_context(self, state: State, error: dict) -> ModelInput: ...
    def add_historical_context(self, state: State) -> ModelInput: ...
    def record_failure(self, state: State, error: dict) -> State: ...
    def advance_step(self, state: State, result: dict) -> State: ...
    def is_complete(self, state: State) -> bool: ...
```

- ToolRegistry
    - Methods: register, get, list; returns typed callables with schemas for structured tool calling.

```python
class ToolRegistry(Protocol):
    def register(self, tool: ToolSpec) -> None: ...
    def get(self, name: str) -> ToolCallable: ...
    def list(self) -> list[ToolSpec]: ...
```

- Planner, Executor, Evaluator, ErrorClassifier, EscalationHandler, Tracer
    - Define narrow interfaces that the LangGraph nodes invoke.


## Factories (config‑driven wiring)

- make_graph_store(cfg) → GraphStore (neo4j, in‑memory) - located in `graph/graph_store_factory.py`
- make_context_manager(cfg) → ContextManager (policy: disclosure limits, retry thresholds) - located in `context/context_manager_factory.py`
- make_tool_registry(cfg) → ToolRegistry (bind to chat model once) - located in `tools/tool_registry_factory.py`
- make_tracer(cfg) → Tracer (Langfuse‑backed, console, or no‑op) - located in `observability/tracer_factory.py`
- make_agent(cfg) → CompiledGraph (assemble nodes/edges; attach callbacks/tracer; enable checkpointer) - located in `agents/agent_factory.py`

Snippet:

```python
def make_graph_store(cfg: GraphStoreConfig) -> GraphStore:
    if cfg.kind == "neo4j":
        # TODO: Implement Neo4j graph store
        raise NotImplementedError("Neo4j graph store not yet implemented")
    elif cfg.kind == "memory":
        from .in_memory_graph import InMemoryGraphStore
        return InMemoryGraphStore()
    else:
        raise ValueError(f"Unsupported graph store type: {cfg.kind}")
```


## Data Models: Common UUIDv4 Base

- All domain entities inherit a base class that injects a code‑controlled UUIDv4 id.
- IDs are created in code (not by the LLM) and validated at the boundary; ensure immutability post‑creation.
- Track created_at/updated_at; update timestamps atomically at write time.

Snippet (Pydantic example):

```python
from uuid import uuid4, UUID
from datetime import datetime
from pydantic import BaseModel, Field

class BaseEntity(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        frozen = True  # id immutability; consider model_copy(update=...) for updates
```

Derivations: Node, Edge, NodeSpec, EdgeSpec, Patch inherit fields and enforce invariants (labels, keys, props).

## Tools and Contracts

- GraphStore: add_node, add_edge, update_props, delete with Pydantic schemas; returns BaseEntity‑derived results; human‑readable, actionable error messages.
- CypherQA: NL → Cypher → execute → answer; results explicitly typed; errors guide corrective actions.
- Bind tools to the chat model; validate structured inputs before execution; redact sensitive data in spans.

Snippet (binding):

```python
llm = chat_model.bind_tools([add_node, add_edge, update_props, delete, cypher_qa])
```


## Neo4j Semantics

- Use MERGE with stable natural keys; no duplicate writes on retries.
- Encapsulate Cypher in GraphStore; never construct Cypher strings inside nodes.
- Map database errors to typed domain errors and normalized, human‑readable messages.

Snippet (MERGE pattern):

```cypher
MERGE (t:Ticket {key: $key})
ON CREATE SET t += $props, t.created_at = timestamp()
ON MATCH  SET t += $props, t.updated_at = timestamp()
```


## Flow Control and Recovery

- Conditional edges and Command for atomic update+goto semantics.
- Checkpointer for durable memory and deterministic resume after interrupt or crash.
- Interrupt gates for human‑in‑the‑loop with state snapshot and clean continuation.


## Directory Layout

- /puntini/
    - agents/ (agent_factory.py)
    - api/ (app.py, auth.py, session.py, websocket.py, models.py, README.md)
    - context/ (context_manager.py, context_manager_factory.py)
    - graph/ (graph_store_factory.py, in_memory_graph.py)
    - interfaces/ (context_manager.py, error_classifier.py, escalation.py, evaluator.py, executor.py, graph_store.py, planner.py, tool_registry.py, tracer.py)
    - llm/ (llm_models.py)
    - logging/ (custom_formatter.py, formatters.py, handlers.py, logger.py)
    - models/ (base.py, edge.py, entities.py, errors.py, goal_schemas.py, node.py, patch.py, specs.py)
    - nodes/ (answer.py, call_tool.py, diagnose.py, escalate.py, evaluate.py, parse_goal.py, plan_step.py, route_tool.py)
    - observability/ (console_tracer.py, langfuse_callback.py, langfuse_tracer.py, noop_tracer.py, tracer_factory.py)
    - orchestration/ (checkpointer.py, graph.py, reducers.py, state.py)
    - tools/ (cypher_qa.py, tool_registry.py, tool_registry_factory.py)
    - utils/ (settings.py)
    - tests/ (unit/, integration/, e2e/, golden_traces/)
- config.json (configuration file)
- run_server.py (example server startup script)
- cli.py (at root)


## Build Steps for Cursor

- ✅ Create interfaces for all components; add comprehensive docstrings and type hints.
- ✅ Implement factories with configuration objects; wire no‑op or in‑memory defaults for tests.
- ✅ Add BaseEntity and derived models with UUIDv4 id generation in code; prohibit LLM from proposing ids.
- ✅ Assemble the LangGraph skeleton using the interfaces; return Command for update+goto; enable checkpointer.
- ✅ Add Langfuse tracer and attach callback handler to the compiled graph; propagate a trace_id across nested calls.
- ✅ Implement server configuration system with settings integration for FastAPI.
- ⏳ Implement concrete logic for graph nodes (`call_tool`, `evaluate`, `diagnose`, etc.).
- ⏳ Implement concrete backends (Neo4j GraphStore, real ContextManager policies).

**Current Status:**
- Interfaces are defined in `/puntini/interfaces/`
- Factories are implemented and distributed across relevant modules
- BaseEntity model is implemented in `/puntini/models/base.py`
- State schema is defined in `/puntini/orchestration/state.py`
- Graph orchestration skeleton is in `/puntini/orchestration/graph.py` (node logic is mostly placeholder).
- Tracer implementations are in `/puntini/observability/`
- FastAPI server configuration is integrated with settings system in `/puntini/api/app.py`
- Server configuration is managed through `config.json` with `ServerConfig` dataclass


## Coding Standards

- Docstrings on all public APIs with Args/Returns/Raises/Examples; strict type hints.
- Pure functions for nodes where possible; side effects live in tools/stores; keep nodes thin.
- Structured outputs and tool schemas over free‑form JSON; validate at boundaries.
- Deterministic routing; no implicit branching hidden in prompts.
- Redaction of secrets in logs/traces; span attributes must be privacy‑safe.


## Testing and Quality Gates

- Unit tests: interface contracts, factories, BaseEntity invariants (id immutability), state reducers, router decisions.
- E2E tests:
    - “AddEdge Ticket DEPENDS_ON Milestone” produces a valid Patch and idempotent writes on repeat runs.
    - NL question → reasonable Cypher → correct subgraph answer.
    - Failure paths: identical/random/systematic classifications trigger the correct policy.
    - HITL flow pauses and resumes deterministically with checkpointed state.
- Observability tests: traces contain inputs/outputs (redacted), decision points, errors, and metrics; flush on teardown.


## Acceptance Criteria

- ✅ Interfaces and factories exist for all major components; graph skeleton compiles and runs with in‑memory stubs.
- ✅ All data models inherit BaseEntity; ids are UUIDv4 from code; no LLM‑generated ids anywhere.
- ✅ Langfuse traces span the entire run including sub‑agents/tools; a single trace_id links nested spans.
- ⏳ Progressive disclosure is implemented in the `ContextManager`.
- ⏳ Neo4j backend uses MERGE semantics and returns typed, human‑readable error messages.

**Implementation Notes:**
- Graph store factory supports memory implementation, Neo4j pending
- Context manager factory supports simple implementation, progressive pending  
- Tracer factory supports noop, console, and langfuse implementations
- Tool registry factory supports standard and cached implementations
- Agent factory provides both simple and component-based agent creation


## Future Extensions

- GraphRAG and hierarchical summaries for large corpora.
- Auto‑tuning of disclosure policies and retry budgets.
- Scorecards and dashboards in Langfuse for error taxonomy and tool helpfulness.

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


