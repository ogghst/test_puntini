# Graph Store Implementations

This directory contains implementations of the GraphStore interface for different graph database backends.

## Available Implementations

### InMemoryGraphStore

A simple in-memory implementation for testing and development purposes.

```python
from puntini.graph import create_memory_graph_store

store = create_memory_graph_store()
```

### MemgraphGraphStore

A production-ready implementation using Memgraph as the backend graph database.

```python
from puntini.graph import create_memgraph_graph_store

store = create_memgraph_graph_store(
    host="127.0.0.1",
    port=7687,
    username="",  # Optional
    password="",  # Optional
    use_ssl=False
)
```

## Configuration

Graph stores can be configured through the `config.json` file:

```json
{
  "memgraph": {
    "host": "127.0.0.1",
    "port": 7687,
    "username": "",
    "password": "",
    "use_ssl": false
  }
}
```

## Factory Pattern

Use the factory to create graph store instances based on configuration:

```python
from puntini.graph import make_graph_store, GraphStoreConfig

# Create configuration
config = GraphStoreConfig("memgraph", host="localhost", port=7687)

# Create store
store = make_graph_store(config)
```

## Features

All implementations support:

- **Idempotent Operations**: All operations use MERGE semantics to ensure idempotency
- **Transactional Guarantees**: Operations are atomic within transactions
- **Type Safety**: Full type hints and Pydantic model validation
- **Error Handling**: Comprehensive error types for different failure modes
- **Cypher Queries**: Raw Cypher query execution for advanced use cases
- **Subgraph Retrieval**: Extract subgraphs with configurable depth

## Memgraph Setup

### Using Docker (Recommended)

```bash
# Run Memgraph with the platform (includes web interface)
docker run -it -p 7687:7687 -p 3000:3000 memgraph/memgraph-platform

# Or run just the database
docker run -it -p 7687:7687 memgraph/memgraph
```

### Local Installation

See the [Memgraph documentation](https://memgraph.com/docs/installation) for local installation instructions.

## Dependencies

The MemgraphGraphStore requires the `gqlalchemy` package:

```bash
pip install gqlalchemy>=1.4.0
```

## Usage Examples

### Basic Node Operations

```python
from puntini.models.specs import NodeSpec

# Create a node
node_spec = NodeSpec(
    label="Person",
    key="john_doe",
    properties={"name": "John Doe", "age": 30}
)
node = store.upsert_node(node_spec)

# Update properties
store.update_props(
    MatchSpec(label="Person", key="john_doe"),
    {"age": 31, "city": "New York"}
)
```

### Basic Edge Operations

```python
from puntini.models.specs import EdgeSpec

# Create an edge
edge_spec = EdgeSpec(
    relationship_type="KNOWS",
    source_key="john_doe",
    target_key="jane_smith",
    source_label="Person",
    target_label="Person",
    properties={"since": "2020"}
)
edge = store.upsert_edge(edge_spec)
```

### Cypher Queries

```python
# Run a Cypher query
results = store.run_cypher(
    "MATCH (p:Person)-[r:KNOWS]->(friend) RETURN p.name, friend.name",
    {"since": "2020"}
)
```

### Subgraph Retrieval

```python
# Get a subgraph around a central node
subgraph = store.get_subgraph(
    MatchSpec(label="Person", key="john_doe"),
    depth=2
)
```

## Error Handling

The implementation provides specific error types for different scenarios:

- `ValidationError`: Input validation failures
- `ConstraintViolationError`: Database constraint violations
- `NotFoundError`: Resource not found
- `QueryError`: Query execution failures

```python
from puntini.models.errors import ValidationError, NotFoundError

try:
    store.upsert_node(node_spec)
except ValidationError as e:
    print(f"Validation failed: {e.message}")
except NotFoundError as e:
    print(f"Resource not found: {e.message}")
```

## Testing

Run the unit tests for the Memgraph implementation:

```bash
# Run all graph store tests
pytest backend/puntini/tests/unit/test_memgraph_graph.py -v

# Run with coverage
pytest backend/puntini/tests/unit/test_memgraph_graph.py --cov=puntini.graph.memgraph_graph
```

## Performance Considerations

- **Connection Pooling**: The MemgraphGraphStore creates a single connection per instance
- **Transaction Management**: Each operation runs in its own transaction
- **Query Optimization**: Use specific MatchSpecs rather than broad queries when possible
- **Batch Operations**: Consider using the PatchSpec for multiple related operations

## Security

- **Authentication**: Configure username/password for production deployments
- **SSL/TLS**: Enable SSL for encrypted connections in production
- **Network Security**: Restrict database access to trusted networks only
- **Input Validation**: All inputs are validated using Pydantic models

## Monitoring and Observability

The MemgraphGraphStore integrates with the observability system:

- **Tracing**: All operations are traced with Langfuse
- **Logging**: Comprehensive logging for debugging and monitoring
- **Metrics**: Performance metrics for query execution times
- **Error Tracking**: Detailed error reporting with context

## Migration from InMemoryGraphStore

The MemgraphGraphStore implements the same interface as InMemoryGraphStore, making migration straightforward:

```python
# Before (in-memory)
from puntini.graph import create_memory_graph_store
store = create_memory_graph_store()

# After (Memgraph)
from puntini.graph import create_memgraph_graph_store
store = create_memgraph_graph_store()
```

No code changes are required for the graph operations themselves.
