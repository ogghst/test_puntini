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
        from ..tools.graph_ops import InMemoryGraphStore
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
    - interfaces/ (graph_store.py, context_manager.py, tool_registry.py, planner.py, executor.py, evaluator.py, error_classifier.py, escalation.py, tracer.py)
    - models/ (base.py, node.py, edge.py, patch.py, errors.py, specs.py)
    - nodes/ (parse_goal.py, plan_step.py, route_tool.py, call_tool.py, evaluate.py, diagnose.py, escalate.py, answer.py)
    - orchestration/ (state.py, graph.py, reducers.py, checkpointer.py)
    - tools/ (graph_ops.py, cypher_qa.py, tool_registry.py, tool_registry_factory.py)
    - observability/ (langfuse_tracer.py, console_tracer.py, noop_tracer.py, tracer_factory.py)
    - agents/ (agent_factory.py)
    - context/ (context_manager.py, context_manager_factory.py)
    - graph/ (graph_store_factory.py)
    - cli.py, settings.py
    - tests/ (unit/, e2e/, golden_traces/)


## Build Steps for Cursor

- ✅ Create interfaces for all components; add comprehensive docstrings and type hints.
- ✅ Implement factories with configuration objects; wire no‑op or in‑memory defaults for tests.
- ✅ Add BaseEntity and derived models with UUIDv4 id generation in code; prohibit LLM from proposing ids.
- 🔄 Assemble the LangGraph skeleton using the interfaces; return Command for update+goto; enable checkpointer.
- 🔄 Add Langfuse tracer and attach callback handler to the compiled graph; propagate a trace_id across nested calls.
- ⏳ Only after the skeleton is green, implement concrete backends (Neo4j GraphStore, real ContextManager policies, real tools).

**Current Status:**
- Interfaces are defined in `/puntini/interfaces/`
- Factories are implemented and distributed across relevant modules
- BaseEntity model is implemented in `/puntini/models/base.py`
- State schema is defined in `/puntini/orchestration/state.py`
- Graph orchestration skeleton is in `/puntini/orchestration/graph.py`
- Tracer implementations are in `/puntini/observability/`


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
- 🔄 Langfuse traces span the entire run including sub‑agents/tools; a single trace_id links nested spans.
- ⏳ Progressive disclosure implemented across three attempts; escalation via interrupt after threshold; deterministic resume.
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