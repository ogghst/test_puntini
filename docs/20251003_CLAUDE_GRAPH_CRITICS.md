# Critical Analysis: Progressive Context Disclosure & Entity Recognition in Knowledge Graph Agents

I'll provide a skeptical, honest assessment of your agent's design with respect to progressive context disclosure and entity recognition best practices.

## Progressive Context Disclosure: Mixed Implementation

### ✅ What Works Well

**1. Initial Minimal Context Parsing**
Your `parse_goal` node does implement progressive disclosure correctly at entry:
- Takes raw user input without overwhelming context
- Extracts only what's immediately parsable
- Routes based on complexity before loading full context

**2. Incremental Planning**
The `plan_step` → `evaluate` → `plan_step` loop is excellent:
- Only plans one step at a time
- Allows the LLM to adjust based on actual execution results
- Prevents over-commitment to invalid plans

### ❌ Critical Problems

**1. Premature Full Goal Parsing**
Your `parse_goal` node tries to do too much upfront:

```python
class GoalSpec:
    entities: List[EntitySpec]           # Too early!
    constraints: List[ConstraintSpec]    # Too early!
    domain_hints: List[DomainHint]       # Too early!
    estimated_steps: int                 # Too early!
```

**Why this violates progressive disclosure:**
- You're asking the LLM to extract ALL entities before any graph context
- The LLM has no idea what entities already exist in the graph
- This guarantees entity recognition errors and duplicates

**Better approach:**
```python
class InitialGoalParse:
    intent: str                    # Just the what
    complexity: GoalComplexity     # Routing decision only
    requires_graph_context: bool   # Do we need to look at the graph first?
    
# THEN in plan_step, with graph context:
class ContextualizedStepPlan:
    entities: List[EntitySpec]     # NOW extract entities
    existing_matches: List[Node]   # With actual graph matches
    ...
```

**2. No Graph Context Integration**
Your entity extraction happens in a vacuum:

```python
class EntitySpec:
    name: str
    type: EntityType
    properties: Dict[str, Any]
    confidence: float  # Confidence about WHAT? You haven't checked the graph!
```

**This is backwards.** Best practice for knowledge graphs:

1. Parse minimal intent
2. **Query graph for relevant context**
3. THEN extract entities with disambiguation
4. Present options if ambiguous

**Example of what's missing:**
```
User: "Add a relationship between John and the bug"

Current approach:
- parse_goal extracts: Entity(name="John"), Entity(name="bug")
- Blindly proceeds to plan_step
- Creates duplicate "John" node (there were 5 Johns in the graph!)

Better approach:
- parse_goal extracts: Intent("add_relationship"), EntityRef("John"), EntityRef("bug")
- plan_step queries: "Find nodes matching 'John'" → [John Doe, John Smith, John's Tickets...]
- plan_step queries: "Find nodes matching 'bug' with type Issue/Ticket" → [BUG-123, BUG-456]
- LLM disambiguates with user: "Which John? Which bug?"
```

## Entity Recognition: Fundamentally Flawed

### The Core Problem: No Graph Memory

**Your `EntitySpec` has amnesia:**

```python
class EntitySpec:
    name: str           # Just a string!
    type: EntityType    # Guessed from thin air
    label: Optional[str]
    properties: Dict[str, Any]
    confidence: float   # False confidence
```

**What's missing:**
- No reference to existing graph nodes
- No similarity scores to existing entities
- No disambiguation mechanism
- No entity resolution strategy

### Best Practices You're Violating

**1. Entity Linking Before Extraction**

Standard knowledge graph pipeline:
```
Raw Text → Entity Mentions → Entity Candidates → Entity Linking → Resolved Entities
```

Your pipeline:
```
Raw Text → Entity Extraction → ??? → Pray it works
```

**2. No Canonical Entity IDs**

Your entities use human-readable names as identifiers:
```python
EntitySpec(name="John Doe")  # Which John Doe?
```

Best practice:
```python
EntityMention(
    surface_form="John",
    canonical_id=None,  # To be resolved
    candidates=[
        EntityCandidate(id="user:123", name="John Doe", similarity=0.9),
        EntityCandidate(id="user:456", name="John Smith", similarity=0.3),
    ]
)
```

**3. No Deduplication Strategy**

Critical question: What happens when I run these prompts?
```
1. "Create a user John Doe"
2. "Add a ticket reported by John"
3. "Create John Doe's profile"
```

Your system will likely create 3 separate "John" entities. No enterprise knowledge graph can tolerate this.

**You need:**
- Entity resolution rules (match by key, email, unique properties)
- Merge strategies (when are two entities the same?)
- Conflict resolution (which properties win?)

### Specific Critiques

**1. EntityType Enum is Too Simplistic**

```python
class EntityType(str, Enum):
    NODE = "node"
    EDGE = "edge"
    PROPERTY = "property"
    QUERY = "query"
    UNKNOWN = "unknown"
```

**Problems:**
- NODE is not a type—"User", "Ticket", "Project" are types
- EDGE is not an entity type—it's a relationship
- PROPERTY shouldn't be an EntityType
- This enum serves no useful purpose for graph operations

**Better approach:**
```python
class GraphElementType(str, Enum):
    NODE_REFERENCE = "node_ref"      # Reference to existing/new node
    EDGE_REFERENCE = "edge_ref"      # Reference to relationship
    LITERAL_VALUE = "literal"        # Actual value, not entity
    SCHEMA_REFERENCE = "schema_ref"  # Reference to node label/edge type
```

**2. Confidence Scores Are Meaningless**

```python
confidence: float = 1.0  # Based on what??
```

Without graph context, this number is fiction. Real confidence requires:
- String similarity to existing entities
- Property overlap with candidates
- Context from surrounding entities
- User feedback history

**3. No Handling of Ambiguous References**

Your system has no way to ask:
- "Did you mean BUG-123 or BUG-124?"
- "John Smith or John Doe?"
- "Create a new Project or use existing?"

This should be in your state schema but isn't:
```python
class AmbiguityResolution:
    ambiguous_entities: List[EntityMention]
    disambiguation_question: str
    candidates_per_entity: Dict[str, List[EntityCandidate]]
    resolution_status: ResolutionStatus
```

## Data Structure Problems

### State Schema: Information Overload

Your state passes EVERYTHING through EVERY node:

```python
class State:
    goal: str
    plan: List[str]
    progress: List[str]
    failures: List[Failure]
    retry_count: int
    max_retries: int
    messages: List[Any]
    current_step: str
    current_attempt: int
    artifacts: List[Artifact]
    result: Optional[Dict[str, Any]]
    tool_registry: Optional[Any]
    graph_store: Optional[Any]
    context_manager: Optional[Any]
    tracer: Optional[Any]
    # ... 16 more fields
```

**This violates progressive disclosure at the architectural level.**

**Problems:**
1. Nodes receive data they don't need (information overload)
2. Tight coupling between all nodes
3. No clear data flow (everything flows everywhere)
4. Memory inefficiency (dragging full history through every node)

**Better pattern:**
```python
class MinimalState:
    session_id: str
    current_node: str
    shared_services: Services  # Registry, store, etc.

class NodeInput[T]:
    state: MinimalState
    context: T  # Node-specific context only

class ParseGoalInput:
    raw_goal: str
    user_context: UserContext

class PlanStepInput:
    goal_spec: GoalSpec
    graph_snapshot: GraphSnapshot  # Only relevant subgraph
    previous_results: List[StepResult]
```

### Response Objects: Redundant

Every node returns nearly identical responses:
```python
class ParseGoalResponse:
    current_step: str
    progress: List[str]
    artifacts: List[Artifact]
    failures: List[Failure]
    result: ParseGoalResult
    current_attempt: int
```

This is copy-paste architecture. You don't need this level of redundancy.

## Use Case Analysis: Revealing Flaws

### Use Case 1: "Good Prompt"

You claim this works, but let's trace the entity recognition:

**Prompt:** "Create a new 'Ticket' node with the key 'TICKET-123'..."

**Questions your system doesn't ask:**
1. Does TICKET-123 already exist? (duplicate prevention)
2. Is there a JIRA integration that owns this ticket ID? (external system sync)
3. Does the schema require Ticket nodes to have certain mandatory properties? (schema validation)
4. Is john.doe a unique key, or could there be multiple? (entity resolution)

**Your workflow assumes perfect input.** Real-world knowledge graph agents must handle:
- Partial information
- Conflicting information
- Implied relationships
- Schema violations

### Use Case 2: "Bad Prompt"

**Prompt:** "My dashboard is broken. Fix it."

Your analysis:
> "The LLM is unable to extract a clear intent or any specific entities."

**This reveals the core problem:** Your system requires structured, graph-specific input. A good knowledge graph agent should:

1. Recognize "dashboard" as a potential entity
2. Query graph: "Find all Dashboard nodes"
3. Query graph: "Find all 'broken' or 'error' relationships"
4. Ask clarifying questions: "Which dashboard? What's broken about it?"

Instead, you escalate immediately. This is a **failure of progressive context disclosure**—you gave up without using available context.

## Architectural Recommendations

### 1. Add Graph-Aware Entity Resolution Layer

```python
class EntityResolver:
    def resolve(self, mention: str, context: GraphContext) -> EntityResolution:
        # 1. Find candidates in graph
        candidates = self.graph.find_similar(mention)
        
        # 2. Score by context
        scored = self.score_by_context(candidates, context)
        
        # 3. Return resolution strategy
        if len(scored) == 0:
            return CreateNew(mention)
        elif len(scored) == 1 and scored[0].confidence > 0.9:
            return UseExisting(scored[0].id)
        else:
            return AskUser(scored[:5])  # Top 5 candidates
```

### 2. Implement Two-Phase Parsing

**Phase 1: Intent Parsing (No Graph Context)**
```python
parse_goal() → IntentSpec:
    - intent_type: "create" | "query" | "update" | "delete"
    - mentioned_entities: List[str]  # Just strings
    - requires_graph_context: bool
```

**Phase 2: Entity Resolution (With Graph Context)**
```python
resolve_entities(intent, graph_context) → ResolvedGoalSpec:
    - entities: List[ResolvedEntity]  # Linked to graph
    - ambiguities: List[Ambiguity]     # Requires user input
    - ready_to_execute: bool
```

### 3. Add Explicit Disambiguation Node

```
parse_goal → resolve_entities → {
    if ambiguous → disambiguate (wait for user)
    if resolved → plan_step
}
```

### 4. Implement Entity Confidence Properly

```python
class EntityConfidence:
    name_match: float          # String similarity
    type_match: float          # Type compatibility  
    property_match: float      # Property overlap
    context_match: float       # Surrounding entities
    overall: float             # Weighted combination
    
    def is_certain(self) -> bool:
        return self.overall > 0.95
    
    def requires_human(self) -> bool:
        return 0.3 < self.overall < 0.7
```

## Final Verdict

### Strengths
1. ✅ Step-by-step execution loop
2. ✅ Separation of planning and execution
3. ✅ Retry and error handling infrastructure

### Critical Weaknesses
1. ❌ **No graph-aware entity recognition**
2. ❌ **Premature entity extraction without context**
3. ❌ **No entity deduplication or disambiguation**
4. ❌ **False confidence scores**
5. ❌ **Over-complex state management**
6. ❌ **No two-phase parsing**

### Bottom Line

Your agent implements progressive **execution** disclosure (good) but violates progressive **context** disclosure (bad). The entity recognition system is naive and will create duplicate entities, miss existing ones, and fail on ambiguous references.

**This would not survive production use in any real knowledge graph application.**

You need to add graph-aware entity resolution BEFORE the plan_step node, not after. The current architecture assumes the LLM can recognize entities from text alone—this is the fundamental flaw.