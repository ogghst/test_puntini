"""Unit tests for simplified graph orchestration implementation.

This module tests the simplified graph orchestration as specified in Phase 3
of the progressive refactoring plan, ensuring proper state management,
node execution, and routing functionality.
"""

import pytest
from typing import Dict, Any, List
from unittest.mock import Mock, MagicMock, patch

from puntini.orchestration.simplified_graph import (
    parse_intent, resolve_entities, disambiguate, plan_step, execute_tool,
    evaluate, diagnose, escalate, answer,
    route_after_parse_intent, route_after_resolve_entities, 
    route_after_disambiguate, route_after_diagnose,
    create_simplified_agent_graph, create_simplified_production_agent
)
from puntini.orchestration.simplified_state import (
    SimplifiedState, create_simplified_state
)
from puntini.orchestration.minimal_state import Services
from puntini.models.goal_schemas import TodoItem
from puntini.nodes.message import Artifact, Failure, ErrorContext, EscalateContext


class TestSimplifiedNodes:
    """Test cases for simplified node implementations."""
    
    def create_mock_state(self) -> SimplifiedState:
        """Create a mock simplified state for testing."""
        services = Services(
            tool_registry=Mock(),
            context_manager=Mock(),
            tracer=Mock(),
            graph_store=Mock()
        )
        
        return create_simplified_state(
            session_id="test-session",
            goal="Create a new user",
            shared_services=services,
            retry_count=0,
            max_retries=3
        )
    
    def create_mock_response(self, node_name: str, status: str = "success") -> Mock:
        """Create a mock response object for testing."""
        mock_response = Mock()
        mock_response.current_step = "next_node"
        mock_response.current_attempt = 1
        mock_response.progress = [f"{node_name} completed"]
        mock_response.artifacts = [{"type": "test", "data": "test_data"}]
        mock_response.failures = []
        
        # Create mock result
        mock_result = Mock()
        mock_result.model_dump.return_value = {"status": status, "data": "test_result"}
        mock_response.result = mock_result
        
        return mock_response
    
    @patch('puntini.orchestration.simplified_graph.parse_intent_impl')
    def test_parse_intent_node(self, mock_parse_intent_impl):
        """Test parse_intent node execution."""
        # Setup
        state = self.create_mock_state()
        mock_response = self.create_mock_response("parse_intent")
        mock_response.result.intent_type = "create"
        mock_parse_intent_impl.return_value = mock_response
        
        # Execute
        result = parse_intent(state)
        
        # Verify
        assert result["current_step"] == "next_node"
        assert result["current_attempt"] == 1
        assert len(result["progress"]) == 1
        assert result["progress"][0] == "Parsed intent: create"
        assert len(result["artifacts"]) == 1
        assert result["result"]["status"] == "success"
        assert result["current_node"] == "parse_intent"
    
    @patch('puntini.orchestration.simplified_graph.resolve_entities_impl')
    def test_resolve_entities_node(self, mock_resolve_entities_impl):
        """Test resolve_entities node execution."""
        # Setup
        state = self.create_mock_state()
        mock_response = self.create_mock_response("resolve_entities")
        
        # Mock result with entities
        mock_result = Mock()
        mock_result.entities = [{"id": "1", "name": "entity1"}, {"id": "2", "name": "entity2"}]
        mock_result.model_dump.return_value = {"status": "success", "entities": mock_result.entities}
        mock_response.result = mock_result
        mock_resolve_entities_impl.return_value = mock_response
        
        # Execute
        result = resolve_entities(state)
        
        # Verify
        assert result["current_step"] == "next_node"
        assert len(result["progress"]) == 1
        assert "Resolved entities: 2 entities" in result["progress"][0]
        assert result["result"]["status"] == "success"
        assert len(result["result"]["entities"]) == 2
        assert result["current_node"] == "resolve_entities"
    
    @patch('puntini.orchestration.simplified_graph.disambiguate_impl')
    def test_disambiguate_node(self, mock_disambiguate_impl):
        """Test disambiguate node execution."""
        # Setup
        state = self.create_mock_state()
        mock_response = self.create_mock_response("disambiguate")
        mock_response.result.status = "resolved"
        mock_disambiguate_impl.return_value = mock_response
        
        # Execute
        result = disambiguate(state)
        
        # Verify
        assert result["current_step"] == "next_node"
        assert len(result["progress"]) == 1
        assert "Disambiguation completed: resolved" in result["progress"][0]
        assert result["result"]["status"] == "success"
        assert result["current_node"] == "disambiguate"
    
    @patch('puntini.orchestration.simplified_graph.plan_step_impl')
    def test_plan_step_node(self, mock_plan_step_impl):
        """Test plan_step node execution."""
        # Setup
        state = self.create_mock_state()
        mock_response = self.create_mock_response("plan_step")
        
        # Mock tool signature
        mock_tool_signature = Mock()
        mock_tool_signature.tool_name = "create_node"
        mock_tool_signature.model_dump.return_value = {"tool_name": "create_node", "tool_args": {}}
        mock_response.tool_signature = mock_tool_signature
        mock_plan_step_impl.return_value = mock_response
        
        # Execute
        result = plan_step(state)
        
        # Verify
        assert result["current_step"] == "next_node"
        assert len(result["progress"]) == 1
        assert "Planned step: create_node" in result["progress"][0]
        assert result["tool_signature"]["tool_name"] == "create_node"
        assert result["current_node"] == "plan_step"
    
    def test_execute_tool_node_success(self):
        """Test execute_tool node with successful execution."""
        # Setup
        state = self.create_mock_state()
        state["tool_signature"] = {
            "tool_name": "create_node",
            "tool_args": {"label": "User", "properties": {"name": "John"}}
        }
        
        # Mock tool registry and tool
        mock_tool = Mock()
        mock_tool.execute.return_value = {"node_id": "123", "status": "created"}
        
        mock_tool_registry = Mock()
        mock_tool_registry.get.return_value = mock_tool
        state["shared_services"]["tool_registry"] = mock_tool_registry
        
        # Execute
        result = execute_tool(state)
        
        # Verify
        assert result["current_node"] == "execute_tool"
        assert len(result["progress"]) == 1
        assert "Executed tool 'create_node' successfully" in result["progress"][0]
        assert result["result"]["status"] == "success"
        assert result["result"]["tool_name"] == "create_node"
        assert result["result"]["result"]["node_id"] == "123"
        
        # Verify tool was called correctly
        mock_tool.execute.assert_called_once_with(label="User", properties={"name": "John"})
    
    def test_execute_tool_node_tool_not_found(self):
        """Test execute_tool node when tool is not found."""
        # Setup
        state = self.create_mock_state()
        state["tool_signature"] = {
            "tool_name": "nonexistent_tool",
            "tool_args": {}
        }
        
        # Mock tool registry that returns None
        mock_tool_registry = Mock()
        mock_tool_registry.get.return_value = None
        state["shared_services"]["tool_registry"] = mock_tool_registry
        
        # Execute
        result = execute_tool(state)
        
        # Verify
        assert result["current_node"] == "execute_tool"
        assert len(result["progress"]) == 1
        assert "Tool execution failed: Tool 'nonexistent_tool' not found" in result["progress"][0]
        assert len(result["failures"]) == 1
        assert result["failures"][0]["type"] == "execution_error"
        assert result["failures"][0]["tool_name"] == "nonexistent_tool"
    
    def test_execute_tool_node_no_registry(self):
        """Test execute_tool node when no tool registry is available."""
        # Setup
        state = self.create_mock_state()
        state["shared_services"]["tool_registry"] = None
        
        # Execute
        result = execute_tool(state)
        
        # Verify
        assert result["current_node"] == "execute_tool"
        assert len(result["progress"]) == 1
        assert "Error: No tool registry available" in result["progress"][0]
        assert len(result["failures"]) == 1
        assert result["failures"][0]["type"] == "system_error"
    
    @patch('puntini.orchestration.simplified_graph.evaluate_impl')
    def test_evaluate_node(self, mock_evaluate_impl):
        """Test evaluate node execution."""
        # Setup
        state = self.create_mock_state()
        mock_response = self.create_mock_response("evaluate")
        
        # Mock result with next action
        mock_result = Mock()
        mock_result.next_action = "plan_step"
        mock_result.retry_count = 1
        mock_result.model_dump.return_value = {"status": "success", "next_action": "plan_step", "retry_count": 1}
        mock_response.result = mock_result
        mock_response.todo_list = [{"id": "1", "task": "next step"}]
        mock_evaluate_impl.return_value = mock_response
        
        # Execute
        result = evaluate(state)
        
        # Verify Command is returned
        assert hasattr(result, 'update')
        assert hasattr(result, 'goto')
        assert result.goto == "next_node"
        
        # Verify state updates
        assert result.update["current_step"] == "next_node"
        assert len(result.update["progress"]) == 1
        assert "Evaluation completed: plan_step" in result.update["progress"][0]
        assert result.update["retry_count"] == 1
        assert len(result.update["todo_list"]) == 1
    
    @patch('puntini.orchestration.simplified_graph.diagnose_impl')
    def test_diagnose_node(self, mock_diagnose_impl):
        """Test diagnose node execution."""
        # Setup
        state = self.create_mock_state()
        mock_response = self.create_mock_response("diagnose")
        
        # Mock error context
        mock_error_context = Mock()
        mock_error_context.type = "systematic"
        mock_error_context.model_dump.return_value = {"type": "systematic", "message": "test error"}
        mock_response.error_context = mock_error_context
        mock_diagnose_impl.return_value = mock_response
        
        # Execute
        result = diagnose(state)
        
        # Verify
        assert result["current_node"] == "diagnose"
        assert len(result["progress"]) == 1
        assert "Diagnosis completed: systematic error" in result["progress"][0]
        assert result["error_context"]["type"] == "systematic"
    
    @patch('puntini.orchestration.simplified_graph.escalate_impl')
    @patch('puntini.orchestration.simplified_graph.interrupt')
    def test_escalate_node(self, mock_interrupt, mock_escalate_impl):
        """Test escalate node execution."""
        # Setup
        state = self.create_mock_state()
        mock_response = self.create_mock_response("escalate")
        
        # Mock escalation context
        mock_escalation_context = Mock()
        mock_escalation_context.model_dump.return_value = {"reason": "tool_failed", "user_input_required": True}
        mock_response.escalation_context = mock_escalation_context
        mock_escalate_impl.return_value = mock_response
        
        # Execute
        result = escalate(state)
        
        # Verify Command is returned
        assert hasattr(result, 'update')
        assert hasattr(result, 'goto')
        assert result.goto == "next_node"
        
        # Verify interrupt was called
        mock_interrupt.assert_called_once()
        
        # Verify state updates
        assert result.update["current_step"] == "next_node"
        assert len(result.update["progress"]) == 1
        assert "Escalation: unknown" in result.update["progress"][0]
        assert result.update["escalation_context"]["reason"] == "tool_failed"
    
    @patch('puntini.orchestration.simplified_graph.answer_impl')
    def test_answer_node(self, mock_answer_impl):
        """Test answer node execution."""
        # Setup
        state = self.create_mock_state()
        mock_response = self.create_mock_response("answer")
        mock_answer_impl.return_value = mock_response
        
        # Execute
        result = answer(state)
        
        # Verify
        assert result["current_node"] == "answer"
        assert len(result["progress"]) == 1
        assert "Final answer: success" in result["progress"][0]
        assert result["result"]["status"] == "success"


class TestRoutingFunctions:
    """Test cases for routing functions."""
    
    def create_mock_state(self, result_data: Dict[str, Any] = None) -> SimplifiedState:
        """Create a mock simplified state for routing tests."""
        services = Services(
            tool_registry=Mock(),
            context_manager=Mock(),
            tracer=Mock(),
            graph_store=Mock()
        )
        
        state = create_simplified_state(
            session_id="test-session",
            goal="Test goal",
            shared_services=services
        )
        
        if result_data:
            state["result"] = result_data
        
        return state
    
    def test_route_after_parse_intent_success_with_graph_context(self):
        """Test routing after parse_intent when graph context is required."""
        state = self.create_mock_state({
            "status": "success",
            "intent_type": "create",
            "requires_graph_context": True
        })
        
        result = route_after_parse_intent(state)
        assert result == "resolve_entities"
    
    def test_route_after_parse_intent_success_without_graph_context(self):
        """Test routing after parse_intent when no graph context is required."""
        state = self.create_mock_state({
            "status": "success",
            "intent_type": "create",
            "requires_graph_context": False
        })
        
        result = route_after_parse_intent(state)
        assert result == "plan_step"
    
    def test_route_after_parse_intent_error(self):
        """Test routing after parse_intent when parsing fails."""
        state = self.create_mock_state({
            "status": "error",
            "message": "parsing failed"
        })
        
        result = route_after_parse_intent(state)
        assert result == "diagnose"
    
    def test_route_after_parse_intent_no_result(self):
        """Test routing after parse_intent when no result is available."""
        state = self.create_mock_state()
        
        result = route_after_parse_intent(state)
        assert result == "diagnose"
    
    def test_route_after_resolve_entities_with_ambiguities(self):
        """Test routing after resolve_entities when ambiguities exist."""
        state = self.create_mock_state({
            "status": "success",
            "has_ambiguities": True,
            "entities": [{"id": "1", "name": "entity1"}]
        })
        
        result = route_after_resolve_entities(state)
        assert result == "disambiguate"
    
    def test_route_after_resolve_entities_no_ambiguities(self):
        """Test routing after resolve_entities when no ambiguities exist."""
        state = self.create_mock_state({
            "status": "success",
            "has_ambiguities": False,
            "entities": [{"id": "1", "name": "entity1"}]
        })
        
        result = route_after_resolve_entities(state)
        assert result == "plan_step"
    
    def test_route_after_resolve_entities_error(self):
        """Test routing after resolve_entities when resolution fails."""
        state = self.create_mock_state({
            "status": "error",
            "message": "resolution failed"
        })
        
        result = route_after_resolve_entities(state)
        assert result == "diagnose"
    
    def test_route_after_disambiguate_success(self):
        """Test routing after disambiguate when disambiguation succeeds."""
        state = self.create_mock_state({
            "status": "success",
            "resolved_entities": [{"id": "1", "name": "entity1"}]
        })
        
        result = route_after_disambiguate(state)
        assert result == "plan_step"
    
    def test_route_after_disambiguate_error(self):
        """Test routing after disambiguate when disambiguation fails."""
        state = self.create_mock_state({
            "status": "error",
            "message": "disambiguation failed"
        })
        
        result = route_after_disambiguate(state)
        assert result == "diagnose"
    
    def test_route_after_diagnose_random_error(self):
        """Test routing after diagnose when error is random."""
        state = self.create_mock_state()
        state["error_context"] = {"type": "random", "message": "random error"}
        
        result = route_after_diagnose(state)
        assert result == "plan_step"
    
    def test_route_after_diagnose_systematic_error(self):
        """Test routing after diagnose when error is systematic."""
        state = self.create_mock_state()
        state["error_context"] = {"type": "systematic", "message": "systematic error"}
        
        result = route_after_diagnose(state)
        assert result == "escalate"
    
    def test_route_after_diagnose_identical_error(self):
        """Test routing after diagnose when error is identical."""
        state = self.create_mock_state()
        state["error_context"] = {"type": "identical", "message": "identical error"}
        
        result = route_after_diagnose(state)
        assert result == "escalate"
    
    def test_route_after_diagnose_unknown_error(self):
        """Test routing after diagnose when error type is unknown."""
        state = self.create_mock_state()
        state["error_context"] = {"type": "unknown", "message": "unknown error"}
        
        result = route_after_diagnose(state)
        assert result == "escalate"


class TestSimplifiedGraphCreation:
    """Test cases for simplified graph creation functions."""
    
    def test_create_simplified_agent_graph(self):
        """Test creating a simplified agent graph."""
        graph = create_simplified_agent_graph()
        
        # Verify graph is created
        assert graph is not None
        
        # Verify nodes are added
        nodes = list(graph.nodes.keys())
        expected_nodes = [
            "parse_intent", "resolve_entities", "disambiguate", "plan_step",
            "execute_tool", "evaluate", "diagnose", "escalate", "answer"
        ]
        
        for expected_node in expected_nodes:
            assert expected_node in nodes
    
    def test_create_simplified_agent_graph_with_checkpointer(self):
        """Test creating a simplified agent graph with checkpointer."""
        mock_checkpointer = Mock()
        
        graph = create_simplified_agent_graph(checkpointer=mock_checkpointer)
        
        # Verify graph is created
        assert graph is not None
        
        # Verify nodes are added
        nodes = list(graph.nodes.keys())
        assert "parse_intent" in nodes
        assert "execute_tool" in nodes  # This should exist (merged from route_tool + call_tool)
    
    @patch('puntini.orchestration.simplified_graph.create_checkpointer')
    @patch('puntini.orchestration.simplified_graph.make_tracer')
    def test_create_simplified_production_agent(self, mock_make_tracer, mock_create_checkpointer):
        """Test creating a simplified production agent."""
        # Setup mocks
        mock_checkpointer = Mock()
        mock_tracer = Mock()
        mock_create_checkpointer.return_value = mock_checkpointer
        mock_make_tracer.return_value = mock_tracer
        
        # Execute
        graph = create_simplified_production_agent(
            checkpointer_type="memory",
            tracer_type="langfuse",
            recursion_limit=10
        )
        
        # Verify
        assert graph is not None
        mock_create_checkpointer.assert_called_once_with("memory")
        mock_make_tracer.assert_called_once()
        
        # Verify nodes are added
        nodes = list(graph.nodes.keys())
        assert "parse_intent" in nodes
        assert "execute_tool" in nodes  # Merged node should exist
        assert "evaluate" in nodes
        assert "diagnose" in nodes
        assert "escalate" in nodes
        assert "answer" in nodes
    
    @patch('puntini.orchestration.simplified_graph.create_checkpointer')
    @patch('puntini.orchestration.simplified_graph.make_tracer')
    def test_create_simplified_production_agent_tracer_fallback(self, mock_make_tracer, mock_create_checkpointer):
        """Test creating a simplified production agent with tracer fallback."""
        # Setup mocks
        mock_checkpointer = Mock()
        mock_create_checkpointer.return_value = mock_checkpointer
        
        # Make tracer creation fail
        mock_make_tracer.side_effect = Exception("Tracer creation failed")
        
        # Execute (should not raise exception due to fallback)
        graph = create_simplified_production_agent(
            checkpointer_type="memory",
            tracer_type="langfuse"
        )
        
        # Verify
        assert graph is not None
        assert mock_make_tracer.call_count == 2  # First call fails, second call succeeds with noop


if __name__ == "__main__":
    pytest.main([__file__])
