# Entity Resolution System

A graph-aware entity resolution system that addresses fundamental flaws in traditional entity recognition approaches. This system implements proper entity linking, disambiguation, and confidence scoring based on graph context.

## Overview

The entity resolution system follows the standard knowledge graph pipeline:
```
Raw Text → Entity Mentions → Entity Candidates → Entity Linking → Resolved Entities
```

### Key Features

- **Graph-aware entity recognition** before planning
- **Proper entity deduplication** and disambiguation
- **Progressive context disclosure** (intent → graph context → entities)
- **Meaningful confidence scores** based on graph similarity
- **Handling of ambiguous references** with user interaction

## Core Components

### 1. Models (`models.py`)

#### GraphElementType
Semantic types for graph elements (replaces simplistic EntityType enum):

```python
from puntini.entity_resolution import GraphElementType

# Available types
GraphElementType.NODE_REFERENCE    # Reference to existing/new node
GraphElementType.EDGE_REFERENCE    # Reference to relationship
GraphElementType.LITERAL_VALUE     # Actual value, not entity
GraphElementType.SCHEMA_REFERENCE  # Reference to node label/edge type
```

#### EntityConfidence
Multi-dimensional confidence scoring:

```python
from puntini.entity_resolution import EntityConfidence

confidence = EntityConfidence(
    name_match=0.8,      # String similarity to existing entities
    type_match=0.9,      # Type compatibility score
    property_match=0.7,  # Property overlap score
    context_match=0.6,   # Context similarity
    overall=0.75         # Weighted combination
)

# Check confidence levels
if confidence.is_certain():
    print("High confidence - can auto-resolve")
elif confidence.requires_human():
    print("Medium confidence - needs user input")
elif confidence.is_too_low():
    print("Low confidence - create new entity")
```

#### EntityMention
Represents a mention of an entity in text:

```python
from puntini.entity_resolution import EntityMention, GraphElementType

mention = EntityMention(
    surface_form="John Doe",
    element_type=GraphElementType.NODE_REFERENCE,
    context={"sentence": "John Doe is working on the project"}
)
```

#### EntityCandidate
Represents a potential match in the graph:

```python
from puntini.entity_resolution import EntityCandidate

candidate = EntityCandidate(
    id="user:123",
    name="John Doe",
    label="User",
    similarity=0.85,
    properties={"email": "john@example.com", "role": "developer"}
)
```

#### EntityResolution
Represents the resolution strategy and result:

```python
from puntini.entity_resolution import EntityResolution, ResolutionStrategy

resolution = EntityResolution(
    strategy=ResolutionStrategy.USE_EXISTING,
    entity_id="user:123",
    confidence=confidence,
    reasoning="High confidence match found: John Doe (similarity: 0.85)"
)
```

### 2. Graph Context (`context.py`)

#### GraphSnapshot
A snapshot of relevant graph data for entity resolution:

```python
from puntini.entity_resolution import GraphSnapshot
from puntini.models.node import Node
from puntini.models.edge import Edge

# Create nodes
node1 = Node(
    id=uuid4(),
    label="User",
    key="user:123",
    properties={"name": "John Doe", "email": "john@example.com"}
)

node2 = Node(
    id=uuid4(),
    label="Project",
    key="project:456",
    properties={"name": "Test Project", "status": "active"}
)

# Create snapshot
snapshot = GraphSnapshot(
    nodes=[node1, node2],
    edges=[],
    context_depth=1
)

# Query the snapshot
user_node = snapshot.get_node_by_id("user:123")
user_nodes = snapshot.get_nodes_by_label("User")
```

#### GraphContext
Context information from the graph for entity resolution:

```python
from puntini.entity_resolution import GraphContext

context = GraphContext(
    snapshot=snapshot,
    entity_similarities={
        "John": [
            {"id": "user:123", "name": "John Doe", "similarity": 0.9},
            {"id": "user:456", "name": "John Smith", "similarity": 0.7}
        ]
    },
    schema_info={
        "labels": ["User", "Project", "Task"],
        "relationship_types": ["MEMBER_OF", "ASSIGNED_TO", "DEPENDS_ON"]
    }
)

# Find similar entities
similar_entities = context.find_similar_entities("John", threshold=0.8)
```

### 3. Similarity Scoring (`similarity.py`)

#### EntitySimilarityScorer
Scores similarity between entity mentions and graph entities:

```python
from puntini.entity_resolution import EntitySimilarityScorer, SimilarityConfig

# Configure similarity scoring
config = SimilarityConfig(
    name_weight=0.4,
    type_weight=0.3,
    property_weight=0.2,
    context_weight=0.1,
    min_similarity_threshold=0.3,
    max_candidates=10
)

scorer = EntitySimilarityScorer(config)

# Score candidates
scored_candidates = scorer.score_mention_candidates(
    mention="John Doe",
    candidates=[candidate1, candidate2],
    context=context
)
```

### 4. Entity Resolution (`resolver.py`)

#### GraphAwareEntityResolver
Main implementation for graph-aware entity resolution:

```python
from puntini.entity_resolution import GraphAwareEntityResolver
from puntini.interfaces.graph_store import GraphStore

# Initialize resolver
resolver = GraphAwareEntityResolver(
    graph_store=graph_store,
    similarity_config=config
)

# Resolve a single mention
resolution = resolver.resolve_mention("John Doe", context)

print(f"Strategy: {resolution.strategy}")
print(f"Entity ID: {resolution.entity_id}")
print(f"Confidence: {resolution.confidence.overall}")
print(f"Reasoning: {resolution.reasoning}")

# Resolve multiple mentions
mentions = ["John Doe", "Test Project", "New Task"]
resolutions = resolver.resolve_mentions(mentions, context)

for resolution in resolutions:
    print(f"Mention: {resolution.mention_id}")
    print(f"Strategy: {resolution.strategy}")
    print(f"Confidence: {resolution.confidence.overall}")
    print("---")
```

#### EntityResolutionService
High-level service for entity resolution operations:

```python
from puntini.entity_resolution import EntityResolutionService

service = EntityResolutionService(resolver)

# Resolve entities from text
text = "John Doe is working on the Test Project and needs to create a new task"
resolutions = service.resolve_entities_from_text(text, context)

for resolution in resolutions:
    print(f"Resolved: {resolution.strategy}")
    print(f"Confidence: {resolution.confidence.overall}")
```

## Complete Example

Here's a complete example showing how to use the entity resolution system:

```python
import uuid
from puntini.entity_resolution import (
    GraphAwareEntityResolver,
    GraphContext,
    GraphSnapshot,
    SimilarityConfig,
    EntityResolutionService
)
from puntini.models.node import Node
from puntini.models.edge import Edge
from puntini.interfaces.graph_store import GraphStore

# 1. Create graph data
user_node = Node(
    id=uuid.uuid4(),
    label="User",
    key="user:123",
    properties={"name": "John Doe", "email": "john@example.com", "role": "developer"}
)

project_node = Node(
    id=uuid.uuid4(),
    label="Project",
    key="project:456",
    properties={"name": "Test Project", "status": "active"}
)

# 2. Create graph snapshot
snapshot = GraphSnapshot(
    nodes=[user_node, project_node],
    edges=[],
    context_depth=1
)

# 3. Create graph context
context = GraphContext(
    snapshot=snapshot,
    entity_similarities={
        "John": [
            {"id": str(user_node.id), "name": "John Doe", "similarity": 0.9}
        ],
        "Test Project": [
            {"id": str(project_node.id), "name": "Test Project", "similarity": 1.0}
        ]
    },
    schema_info={
        "labels": ["User", "Project", "Task"],
        "relationship_types": ["MEMBER_OF", "ASSIGNED_TO", "DEPENDS_ON"]
    }
)

# 4. Configure similarity scoring
config = SimilarityConfig(
    name_weight=0.4,
    type_weight=0.3,
    property_weight=0.2,
    context_weight=0.1,
    min_similarity_threshold=0.3,
    max_candidates=10
)

# 5. Initialize resolver (assuming you have a graph_store)
# resolver = GraphAwareEntityResolver(graph_store, config)
# service = EntityResolutionService(resolver)

# 6. Resolve entities from text
# text = "John Doe is working on the Test Project"
# resolutions = service.resolve_entities_from_text(text, context)

# 7. Process results
# for resolution in resolutions:
#     if resolution.strategy == ResolutionStrategy.USE_EXISTING:
#         print(f"Using existing entity: {resolution.entity_id}")
#     elif resolution.strategy == ResolutionStrategy.CREATE_NEW:
#         print("Creating new entity")
#     elif resolution.strategy == ResolutionStrategy.ASK_USER:
#         print("Need user disambiguation")
```

## Resolution Strategies

The system uses three main resolution strategies:

### 1. USE_EXISTING
- **When**: High confidence match found (similarity > 0.6)
- **Action**: Use the existing entity from the graph
- **Example**: "John Doe" matches existing user with 0.9 similarity

### 2. ASK_USER
- **When**: Medium confidence match (0.3 < similarity < 0.6)
- **Action**: Ask user to disambiguate between candidates
- **Example**: "John" could match "John Doe" or "John Smith"

### 3. CREATE_NEW
- **When**: Low confidence or no candidates found (similarity < 0.3)
- **Action**: Create a new entity
- **Example**: "NewUser123" has no matches in the graph

## Configuration

### SimilarityConfig
Configure how similarity is calculated:

```python
config = SimilarityConfig(
    name_weight=0.4,           # Weight for name similarity
    type_weight=0.3,           # Weight for type similarity
    property_weight=0.2,       # Weight for property similarity
    context_weight=0.1,        # Weight for context similarity
    min_similarity_threshold=0.3,  # Minimum similarity to consider
    max_candidates=10          # Maximum candidates to return
)
```

## Error Handling

The system includes comprehensive error handling:

```python
try:
    resolution = resolver.resolve_mention("John Doe", context)
    if resolution.confidence.is_certain():
        # Proceed with high confidence
        pass
    elif resolution.confidence.requires_human():
        # Ask user for disambiguation
        pass
    else:
        # Create new entity
        pass
except Exception as e:
    print(f"Entity resolution failed: {e}")
```

## Integration with LangGraph

The entity resolution system is designed to integrate with LangGraph nodes:

```python
def parse_goal_with_entity_resolution(state: State) -> State:
    """Parse goal with graph-aware entity resolution."""
    # Extract intent first (no graph context)
    intent = extract_intent(state["goal"])
    
    # Get graph context
    context = get_graph_context(state)
    
    # Resolve entities with graph context
    service = EntityResolutionService(resolver)
    resolutions = service.resolve_entities_from_text(state["goal"], context)
    
    # Update state with resolved entities
    state["resolved_entities"] = resolutions
    return state
```

## Best Practices

1. **Progressive Context Disclosure**: Start with minimal context, add more as needed
2. **Confidence Thresholds**: Use appropriate thresholds for your use case
3. **Error Handling**: Always handle low confidence and ambiguous cases
4. **Performance**: Limit context depth and candidate count for large graphs
5. **User Experience**: Provide clear disambiguation questions for ambiguous cases

## Testing

The system includes comprehensive unit tests:

```bash
# Run all entity resolution tests
pytest tests/unit/entity_resolution/ -v

# Run specific test modules
pytest tests/unit/entity_resolution/test_models.py -v
pytest tests/unit/entity_resolution/test_resolver.py -v
pytest tests/unit/entity_resolution/test_similarity.py -v
pytest tests/unit/entity_resolution/test_context.py -v
```

## Future Enhancements

- **NLP Integration**: Use spaCy or similar for better entity extraction
- **Machine Learning**: Train models for better similarity scoring
- **Caching**: Cache similarity scores for performance
- **Batch Processing**: Process multiple texts efficiently
- **Custom Similarity**: Allow custom similarity functions
