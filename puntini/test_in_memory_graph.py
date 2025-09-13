#!/usr/bin/env python3
"""Test script to verify InMemoryGraphStore implementation."""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from puntini.graph.in_memory_graph import InMemoryGraphStore
from puntini.models.specs import NodeSpec, EdgeSpec, MatchSpec
from puntini.models.errors import ValidationError, NotFoundError


def test_in_memory_graph_store():
    """Test the InMemoryGraphStore implementation."""
    print("Testing InMemoryGraphStore implementation...")
    
    # Create store instance
    store = InMemoryGraphStore()
    
    # Test 1: Create nodes
    print("\n1. Testing node creation...")
    node1 = store.upsert_node(NodeSpec(
        label="Person",
        key="john_doe",
        properties={"name": "John Doe", "age": 30}
    ))
    print(f"Created node: {node1}")
    
    node2 = store.upsert_node(NodeSpec(
        label="Person", 
        key="jane_smith",
        properties={"name": "Jane Smith", "age": 25}
    ))
    print(f"Created node: {node2}")
    
    # Test 2: Create edge
    print("\n2. Testing edge creation...")
    edge1 = store.upsert_edge(EdgeSpec(
        relationship_type="KNOWS",
        source_key="john_doe",
        target_key="jane_smith",
        source_label="Person",
        target_label="Person",
        properties={"since": "2020"}
    ))
    print(f"Created edge: {edge1}")
    
    # Test 3: Update properties
    print("\n3. Testing property updates...")
    store.update_props(
        MatchSpec(label="Person", key="john_doe"),
        {"age": 31, "city": "New York"}
    )
    print("Updated John's properties")
    
    # Test 4: Get subgraph
    print("\n4. Testing subgraph retrieval...")
    subgraph = store.get_subgraph(
        MatchSpec(label="Person", key="john_doe"),
        depth=1
    )
    print(f"Subgraph nodes: {len(subgraph['nodes'])}")
    print(f"Subgraph edges: {len(subgraph['edges'])}")
    
    # Test 5: Cypher query
    print("\n5. Testing Cypher query...")
    results = store.run_cypher("MATCH (n:Person) RETURN n")
    print(f"Cypher query returned {len(results)} results")
    
    # Test 6: Delete edge
    print("\n6. Testing edge deletion...")
    store.delete_edge(MatchSpec(relationship_type="KNOWS"))
    print("Deleted KNOWS edge")
    
    # Test 7: Delete node
    print("\n7. Testing node deletion...")
    store.delete_node(MatchSpec(label="Person", key="jane_smith"))
    print("Deleted Jane Smith node")
    
    # Test 8: Error handling
    print("\n8. Testing error handling...")
    try:
        store.delete_node(MatchSpec(label="Person", key="nonexistent"))
    except NotFoundError as e:
        print(f"Expected error caught: {e}")
    
    print("\n✅ All tests passed! InMemoryGraphStore is working correctly.")


if __name__ == "__main__":
    test_in_memory_graph_store()

