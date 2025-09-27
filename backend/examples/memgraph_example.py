"""Example usage of MemgraphGraphStore implementation.

This script demonstrates how to use the MemgraphGraphStore for basic
graph operations including creating nodes, edges, and running queries.
"""

import sys
import os
from typing import Dict, Any

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from puntini.graph import create_memgraph_graph_store, GraphStoreConfig, make_graph_store
from puntini.models.specs import NodeSpec, EdgeSpec, MatchSpec
from puntini.models.errors import ValidationError, NotFoundError


def demonstrate_memgraph_operations():
    """Demonstrate basic Memgraph operations."""
    print("=== MemgraphGraphStore Example ===\n")
    
    try:
        # Create a MemgraphGraphStore instance
        print("1. Creating MemgraphGraphStore instance...")
        store = create_memgraph_graph_store(
            host="127.0.0.1",
            port=7687,
            username="",  # No authentication by default
            password="",
            use_ssl=False
        )
        print("✓ Connected to Memgraph successfully\n")
        
        # Create nodes
        print("2. Creating nodes...")
        
        # Create a person node
        person_spec = NodeSpec(
            label="Person",
            key="john_doe",
            properties={
                "name": "John Doe",
                "age": 30,
                "email": "john@example.com",
                "city": "New York"
            }
        )
        person_node = store.upsert_node(person_spec)
        print(f"✓ Created person node: {person_node}")
        
        # Create a company node
        company_spec = NodeSpec(
            label="Company",
            key="acme_corp",
            properties={
                "name": "ACME Corporation",
                "industry": "Technology",
                "founded": 2020,
                "employees": 150
            }
        )
        company_node = store.upsert_node(company_spec)
        print(f"✓ Created company node: {company_node}")
        
        # Create a project node
        project_spec = NodeSpec(
            label="Project",
            key="project_alpha",
            properties={
                "name": "Project Alpha",
                "status": "active",
                "budget": 100000,
                "start_date": "2024-01-01"
            }
        )
        project_node = store.upsert_node(project_spec)
        print(f"✓ Created project node: {project_node}\n")
        
        # Create edges
        print("3. Creating edges...")
        
        # Person works for company
        works_for_spec = EdgeSpec(
            relationship_type="WORKS_FOR",
            source_key="john_doe",
            target_key="acme_corp",
            source_label="Person",
            target_label="Company",
            properties={
                "position": "Software Engineer",
                "start_date": "2022-01-15",
                "salary": 75000
            }
        )
        works_for_edge = store.upsert_edge(works_for_spec)
        print(f"✓ Created WORKS_FOR edge: {works_for_edge}")
        
        # Person manages project
        manages_spec = EdgeSpec(
            relationship_type="MANAGES",
            source_key="john_doe",
            target_key="project_alpha",
            source_label="Person",
            target_label="Project",
            properties={
                "role": "Project Manager",
                "responsibility": "Technical Lead",
                "allocation": 0.8
            }
        )
        manages_edge = store.upsert_edge(manages_spec)
        print(f"✓ Created MANAGES edge: {manages_edge}")
        
        # Company owns project
        owns_spec = EdgeSpec(
            relationship_type="OWNS",
            source_key="acme_corp",
            target_key="project_alpha",
            source_label="Company",
            target_label="Project",
            properties={
                "ownership_percentage": 100,
                "investment": 100000
            }
        )
        owns_edge = store.upsert_edge(owns_spec)
        print(f"✓ Created OWNS edge: {owns_edge}\n")
        
        # Update properties
        print("4. Updating node properties...")
        match_spec = MatchSpec(label="Person", key="john_doe")
        store.update_props(match_spec, {"age": 31, "promotion_date": "2024-01-01"})
        print("✓ Updated person properties")
        
        # Get subgraph
        print("5. Retrieving subgraph...")
        subgraph = store.get_subgraph(MatchSpec(label="Person", key="john_doe"), depth=2)
        print(f"✓ Retrieved subgraph with {len(subgraph['nodes'])} nodes and {len(subgraph['edges'])} edges")
        print(f"  Central nodes: {subgraph['central_nodes']}")
        print(f"  Depth: {subgraph['depth']}\n")
        
        # Run Cypher queries
        print("6. Running Cypher queries...")
        
        # Query all nodes
        all_nodes_query = "MATCH (n) RETURN n LIMIT 10"
        all_nodes = store.run_cypher(all_nodes_query)
        print(f"✓ Found {len(all_nodes)} nodes in the graph")
        
        # Query specific relationships
        relationships_query = """
        MATCH (p:Person)-[r]->(target)
        RETURN p.name as person_name, type(r) as relationship_type, 
               target.name as target_name, target.label as target_type
        """
        relationships = store.run_cypher(relationships_query)
        print(f"✓ Found {len(relationships)} relationships")
        for rel in relationships:
            print(f"  {rel['person_name']} -[{rel['relationship_type']}]-> {rel['target_name']} ({rel['target_type']})")
        
        print("\n7. Testing idempotency...")
        # Test idempotency by creating the same node again
        same_person = store.upsert_node(person_spec)
        print(f"✓ Idempotent operation: Same node ID {same_person.id == person_node.id}")
        
        print("\n=== Example completed successfully! ===")
        
    except ValidationError as e:
        print(f"❌ Validation error: {e.message}")
        if e.details:
            print(f"   Details: {e.details}")
    except NotFoundError as e:
        print(f"❌ Not found error: {e.message}")
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
    finally:
        # Clean up connection
        if 'store' in locals():
            store.close()
            print("✓ Connection closed")


def demonstrate_factory_usage():
    """Demonstrate using the factory pattern."""
    print("\n=== Factory Pattern Example ===\n")
    
    try:
        # Using the factory with configuration
        print("1. Using factory with configuration...")
        config = GraphStoreConfig(
            "memgraph",
            host="127.0.0.1",
            port=7687,
            username="",
            password="",
            use_ssl=False
        )
        store = make_graph_store(config)
        print("✓ Created graph store using factory")
        
        # Test basic operation
        test_node = store.upsert_node(NodeSpec(
            label="Test",
            key="factory_test",
            properties={"created_by": "factory_example"}
        ))
        print(f"✓ Created test node: {test_node.id}")
        
        # Clean up
        store.delete_node(MatchSpec(label="Test", key="factory_test"))
        print("✓ Cleaned up test node")
        
        store.close()
        print("✓ Factory example completed successfully!")
        
    except Exception as e:
        print(f"❌ Factory example error: {str(e)}")


if __name__ == "__main__":
    print("MemgraphGraphStore Example Script")
    print("=" * 50)
    
    # Check if Memgraph is running
    print("Note: Make sure Memgraph is running on localhost:7687")
    print("You can start it with: docker run -it -p 7687:7687 memgraph/memgraph-platform\n")
    
    try:
        demonstrate_memgraph_operations()
        demonstrate_factory_usage()
    except KeyboardInterrupt:
        print("\n\nExample interrupted by user")
    except Exception as e:
        print(f"\n❌ Example failed: {str(e)}")
        print("\nMake sure Memgraph is running and accessible at localhost:7687")
