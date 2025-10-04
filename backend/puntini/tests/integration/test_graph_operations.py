"""Integration tests for complex graph operations.

This module contains integration tests that test complex scenarios
and interactions between different graph operations.
"""

import pytest
from typing import Dict, Any, List

from puntini.graph.in_memory_graph import InMemoryGraphStore
from puntini.models.specs import NodeSpec, EdgeSpec, MatchSpec
from puntini.models.errors import ValidationError, NotFoundError


class TestComplexGraphScenarios:
    """Test complex graph scenarios and workflows."""
    
    def test_build_and_query_social_network(self, graph_store: InMemoryGraphStore):
        """Test building and querying a social network graph."""
        # Create people
        people = [
            NodeSpec(label="Person", key="alice", properties={"name": "Alice", "age": 30}),
            NodeSpec(label="Person", key="bob", properties={"name": "Bob", "age": 25}),
            NodeSpec(label="Person", key="charlie", properties={"name": "Charlie", "age": 35}),
            NodeSpec(label="Person", key="diana", properties={"name": "Diana", "age": 28}),
        ]
        
        for person in people:
            graph_store.upsert_node(person)
        
        # Create relationships
        relationships = [
            EdgeSpec(relationship_type="KNOWS", source_key="alice", target_key="bob", source_label="Person", target_label="Person", properties={"since": "2020"}),
            EdgeSpec(relationship_type="KNOWS", source_key="bob", target_key="charlie", source_label="Person", target_label="Person", properties={"since": "2021"}),
            EdgeSpec(relationship_type="KNOWS", source_key="alice", target_key="charlie", source_label="Person", target_label="Person", properties={"since": "2019"}),
            EdgeSpec(relationship_type="KNOWS", source_key="charlie", target_key="diana", source_label="Person", target_label="Person", properties={"since": "2022"}),
        ]
        
        for rel in relationships:
            graph_store.upsert_edge(rel)
        
        # Query Alice's network (depth 1)
        alice_network = graph_store.get_subgraph(MatchSpec(label="Person", key="alice"), depth=1)
        
        assert len(alice_network["nodes"]) == 3  # Alice + 2 direct connections
        assert len(alice_network["edges"]) == 2  # 2 direct relationships
        
        # Query Alice's extended network (depth 2)
        alice_extended = graph_store.get_subgraph(MatchSpec(label="Person", key="alice"), depth=2)
        
        assert len(alice_extended["nodes"]) == 4  # All people
        assert len(alice_extended["edges"]) == 4  # All relationships
    
    def test_company_org_chart_operations(self, graph_store: InMemoryGraphStore):
        """Test building and manipulating a company organizational chart."""
        # Create employees
        employees = [
            NodeSpec(label="Employee", key="ceo", properties={"name": "CEO", "level": "C"}),
            NodeSpec(label="Employee", key="cto", properties={"name": "CTO", "level": "C"}),
            NodeSpec(label="Employee", key="vp_eng", properties={"name": "VP Engineering", "level": "VP"}),
            NodeSpec(label="Employee", key="senior_dev", properties={"name": "Senior Dev", "level": "Senior"}),
            NodeSpec(label="Employee", key="junior_dev", properties={"name": "Junior Dev", "level": "Junior"}),
        ]
        
        for emp in employees:
            graph_store.upsert_node(emp)
        
        # Create reporting relationships
        reports = [
            EdgeSpec(relationship_type="REPORTS_TO", source_key="cto", target_key="ceo", source_label="Employee", target_label="Employee", properties={"since": "2020"}),
            EdgeSpec(relationship_type="REPORTS_TO", source_key="vp_eng", target_key="cto", source_label="Employee", target_label="Employee", properties={"since": "2021"}),
            EdgeSpec(relationship_type="REPORTS_TO", source_key="senior_dev", target_key="vp_eng", source_label="Employee", target_label="Employee", properties={"since": "2022"}),
            EdgeSpec(relationship_type="REPORTS_TO", source_key="junior_dev", target_key="senior_dev", source_label="Employee", target_label="Employee", properties={"since": "2023"}),
        ]
        
        for report in reports:
            graph_store.upsert_edge(report)
        
        # Test organizational queries
        # Find all direct reports of CTO
        cto_reports = graph_store.get_subgraph(MatchSpec(label="Employee", key="cto"), depth=1, direction="incoming")
        assert len(cto_reports["nodes"]) == 2  # CTO + 1 direct report
        
        # Find entire reporting chain from CEO
        ceo_chain = graph_store.get_subgraph(MatchSpec(label="Employee", key="ceo"), depth=4, direction="incoming")
        assert len(ceo_chain["nodes"]) == 5  # All employees
        
        # Test promotion (update properties)
        graph_store.update_props(
            MatchSpec(label="Employee", key="junior_dev"),
            {"level": "Mid", "promoted_date": "2024-01-01"}
        )
        
        # Verify promotion
        for node in graph_store._nodes.values():
            if node.key == "junior_dev":
                assert node.properties["level"] == "Mid"
                assert node.properties["promoted_date"] == "2024-01-01"
                break
        else:
            pytest.fail("Employee not found")
    
    def test_project_dependency_management(self, graph_store: InMemoryGraphStore):
        """Test managing project dependencies and milestones."""
        # Create projects and milestones
        projects = [
            NodeSpec(label="Project", key="project_a", properties={"name": "Project A", "status": "active"}),
            NodeSpec(label="Project", key="project_b", properties={"name": "Project B", "status": "planning"}),
            NodeSpec(label="Project", key="project_c", properties={"name": "Project C", "status": "completed"}),
        ]
        
        milestones = [
            NodeSpec(label="Milestone", key="milestone_1", properties={"name": "Phase 1", "status": "completed"}),
            NodeSpec(label="Milestone", key="milestone_2", properties={"name": "Phase 2", "status": "in_progress"}),
            NodeSpec(label="Milestone", key="milestone_3", properties={"name": "Phase 3", "status": "pending"}),
        ]
        
        for project in projects + milestones:
            graph_store.upsert_node(project)
        
        # Create dependencies
        dependencies = [
            EdgeSpec(relationship_type="DEPENDS_ON", source_key="project_b", target_key="project_a", source_label="Project", target_label="Project", properties={"type": "blocking"}),
            EdgeSpec(relationship_type="DEPENDS_ON", source_key="project_c", target_key="project_b", source_label="Project", target_label="Project", properties={"type": "blocking"}),
            EdgeSpec(relationship_type="HAS_MILESTONE", source_key="project_a", target_key="milestone_1", source_label="Project", target_label="Milestone", properties={"status": "completed"}),
            EdgeSpec(relationship_type="HAS_MILESTONE", source_key="project_a", target_key="milestone_2", source_label="Project", target_label="Milestone", properties={"status": "in_progress"}),
            EdgeSpec(relationship_type="HAS_MILESTONE", source_key="project_b", target_key="milestone_3", source_label="Project", target_label="Milestone", properties={"status": "pending"}),
        ]
        
        for dep in dependencies:
            graph_store.upsert_edge(dep)
        
        # Test dependency queries
        # Find all projects that depend on Project A
        project_a_dependents = graph_store.get_subgraph(MatchSpec(label="Project", key="project_a"), depth=2)
        project_nodes = [n for n in project_a_dependents["nodes"] if n["label"] == "Project"]
        assert len(project_nodes) == 3  # All projects
        
        # Find critical path (blocking dependencies)
        blocking_edges = [e for e in project_a_dependents["edges"] if e.get("properties", {}).get("type") == "blocking"]
        assert len(blocking_edges) == 2  # Two blocking dependencies
        
        # Test milestone completion
        graph_store.update_props(
            MatchSpec(label="Milestone", key="milestone_2"),
            {"status": "completed", "completed_date": "2024-01-15"}
        )
        
        # Verify milestone update
        for node in graph_store._nodes.values():
            if node.key == "milestone_2":
                assert node.properties["status"] == "completed"
                assert node.properties["completed_date"] == "2024-01-15"
                break
        else:
            pytest.fail("Milestone not found")
    
    def test_data_consistency_after_operations(self, graph_store: InMemoryGraphStore):
        """Test that data remains consistent after various operations."""
        # Create initial data
        nodes = [
            NodeSpec(label="A", key="a1", properties={"value": 1}),
            NodeSpec(label="A", key="a2", properties={"value": 2}),
            NodeSpec(label="B", key="b1", properties={"value": 3}),
        ]
        
        for node in nodes:
            graph_store.upsert_node(node)
        
        edges = [
            EdgeSpec(relationship_type="CONNECTS", source_key="a1", target_key="a2", source_label="A", target_label="A", properties={"weight": 1.0}),
            EdgeSpec(relationship_type="CONNECTS", source_key="a2", target_key="b1", source_label="A", target_label="B", properties={"weight": 2.0}),
        ]
        
        for edge in edges:
            graph_store.upsert_edge(edge)
        
        initial_node_count = len(graph_store._nodes)
        initial_edge_count = len(graph_store._edges)
        
        # Perform various operations
        # 1. Update properties
        graph_store.update_props(MatchSpec(label="A"), {"updated": True})
        
        # 2. Add new node and edge
        graph_store.upsert_node(NodeSpec(label="C", key="c1", properties={"value": 4}))
        graph_store.upsert_edge(EdgeSpec(relationship_type="CONNECTS", source_key="b1", target_key="c1", source_label="B", target_label="C", properties={"weight": 3.0}))
        
        # 3. Delete some data
        graph_store.delete_edge(MatchSpec(label="CONNECTS"))
        
        # Verify consistency
        # All nodes should still be valid
        for node in graph_store._nodes.values():
            assert node.id is not None
            assert node.label is not None
            assert node.key is not None
            assert isinstance(node.properties, dict)
        
        # All edges should reference valid nodes
        for edge in graph_store._edges.values():
            assert str(edge.source_id) in graph_store._nodes
            assert str(edge.target_id) in graph_store._nodes
            assert edge.relationship_type is not None
        
        # Key mappings should be consistent
        for node in graph_store._nodes.values():
            expected_key = f"{node.label}:{node.key}"
            assert expected_key in graph_store._node_key_to_id
            assert graph_store._node_key_to_id[expected_key] == node.id
        
        for edge in graph_store._edges.values():
            expected_key = f"{edge.source_label}:{edge.source_key}-[{edge.relationship_type}]->{edge.target_label}:{edge.target_key}"
            assert expected_key in graph_store._edge_key_to_id
            assert graph_store._edge_key_to_id[expected_key] == edge.id
    
    def test_bulk_operations_performance(self, graph_store: InMemoryGraphStore):
        """Test performance and correctness of bulk operations."""
        # Create many nodes
        node_count = 100
        for i in range(node_count):
            node_spec = NodeSpec(
                label="TestNode",
                key=f"node_{i}",
                properties={"index": i, "value": i * 2}
            )
            graph_store.upsert_node(node_spec)
        
        assert len(graph_store._nodes) == node_count
        
        # Create many edges (connect each node to next)
        for i in range(node_count - 1):
            edge_spec = EdgeSpec(
                relationship_type="CONNECTS",
                source_key=f"node_{i}",
                target_key=f"node_{i+1}",
                source_label="TestNode",
                target_label="TestNode",
                properties={"weight": i}
            )
            graph_store.upsert_edge(edge_spec)
        
        assert len(graph_store._edges) == node_count - 1
        
        # Test bulk property updates
        graph_store.update_props(
            MatchSpec(label="TestNode"),
            {"bulk_updated": True}
        )
        
        # Verify all nodes were updated
        for node in graph_store._nodes.values():
            assert node.properties["bulk_updated"] is True
            assert "index" in node.properties  # Original properties preserved
        
        # Test bulk deletions
        # Delete every other node
        for i in range(0, node_count, 2):
            graph_store.delete_node(MatchSpec(key=f"node_{i}"))
        
        # Should have half the nodes and fewer edges
        assert len(graph_store._nodes) == node_count // 2
        assert len(graph_store._edges) < node_count - 1  # Some edges deleted with nodes
    
    def test_error_recovery_and_consistency(self, graph_store: InMemoryGraphStore):
        """Test that the graph remains consistent after error conditions."""
        # Create some initial data
        graph_store.upsert_node(NodeSpec(label="A", key="a1", properties={"value": 1}))
        graph_store.upsert_node(NodeSpec(label="B", key="b1", properties={"value": 2}))
        graph_store.upsert_edge(EdgeSpec(relationship_type="CONNECTS", source_key="a1", target_key="b1", source_label="A", target_label="B", properties={"weight": 1.0}))
        
        initial_node_count = len(graph_store._nodes)
        initial_edge_count = len(graph_store._edges)
        
        # Attempt operations that should fail
        with pytest.raises(ValidationError):
            graph_store.upsert_node(NodeSpec(label="", key="invalid"))
        
        with pytest.raises(NotFoundError):
            graph_store.upsert_edge(EdgeSpec(relationship_type="CONNECTS", source_key="nonexistent", target_key="b1", source_label="A", target_label="B"))
        
        with pytest.raises(NotFoundError):
            graph_store.delete_node(MatchSpec(label="Nonexistent"))
        
        # Graph should remain unchanged after failed operations
        assert len(graph_store._nodes) == initial_node_count
        assert len(graph_store._edges) == initial_edge_count
        
        # All existing data should still be valid
        for node in graph_store._nodes.values():
            assert node.label is not None
            assert node.key is not None
        
        for edge in graph_store._edges.values():
            assert str(edge.source_id) in graph_store._nodes
            assert str(edge.target_id) in graph_store._nodes
    
    def test_concurrent_like_operations(self, graph_store: InMemoryGraphStore):
        """Test operations that simulate concurrent access patterns."""
        # Simulate multiple "threads" creating and updating the same data
        
        # Thread 1: Create initial data
        graph_store.upsert_node(NodeSpec(label="Person", key="alice", properties={"name": "Alice", "version": 1}))
        
        # Thread 2: Try to create same person (should update)
        graph_store.upsert_node(NodeSpec(label="Person", key="alice", properties={"name": "Alice Smith", "version": 2}))
        
        # Thread 3: Try to create same person again (should update)
        graph_store.upsert_node(NodeSpec(label="Person", key="alice", properties={"email": "alice@example.com", "version": 3}))
        
        # Verify final state
        alice_node = None
        for node in graph_store._nodes.values():
            if node.key == "alice":
                alice_node = node
                break
        
        assert alice_node is not None
        assert alice_node.properties["name"] == "Alice Smith"  # Latest name
        assert alice_node.properties["email"] == "alice@example.com"  # Latest email
        assert alice_node.properties["version"] == 3  # Latest version
        
        # Should only have one node with key "alice"
        alice_count = sum(1 for node in graph_store._nodes.values() if node.key == "alice")
        assert alice_count == 1
    
    def test_complex_query_scenarios(self, complex_populated_graph: InMemoryGraphStore):
        """Test complex query scenarios on a populated graph."""
        # Test finding all people who know each other (transitive relationships)
        alice_network = complex_populated_graph.get_subgraph(
            MatchSpec(label="Person", key="alice"), depth=2
        )
        
        # Alice should be connected to Bob and Charlie
        person_keys = [node["key"] for node in alice_network["nodes"] if node["label"] == "Person"]
        assert "alice" in person_keys
        assert "bob" in person_keys
        assert "charlie" in person_keys
        
        # Test finding all skills in the network
        skill_nodes = [node for node in alice_network["nodes"] if node["label"] == "Skill"]
        assert len(skill_nodes) > 0
        
        # Test finding all work relationships
        work_edges = [
            edge for edge in alice_network["edges"] 
            if edge["relationship_type"] == "WORKS_FOR"
        ]
        assert len(work_edges) > 0
        
        # Test Cypher-like queries
        all_people = complex_populated_graph.run_cypher("MATCH (n:Person) RETURN n")
        assert len(all_people) >= 3  # At least Alice, Bob, Charlie
        
        # Test property-based filtering
        complex_populated_graph.update_props(
            MatchSpec(label="Person", properties={"age": 28}),
            {"senior": True}
        )
        
        # Verify update was applied correctly
        senior_people = [
            node for node in complex_populated_graph._nodes.values()
            if node.label == "Person" and node.properties.get("senior") is True
        ]
        assert len(senior_people) > 0