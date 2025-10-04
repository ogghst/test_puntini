"""Unit tests for minimal state pattern implementation.

This module tests the minimal state pattern implementation as specified in Phase 3
of the progressive refactoring plan, ensuring proper state management and
node-specific context handling.
"""

import pytest
from typing import Dict, Any, List
from unittest.mock import Mock, MagicMock

from puntini.orchestration.minimal_state import (
    MinimalState, Services, NodeInput, ParseGoalInput, PlanStepInput,
    ResolveEntitiesInput, ExecuteToolInput, EvaluateInput, DiagnoseInput,
    EscalateInput, AnswerInput, create_node_input, extract_minimal_state,
    merge_node_output
)
from puntini.orchestration.simplified_state import (
    SimplifiedState, create_simplified_state, migrate_from_bloated_state,
    extract_node_context, update_state_with_node_output, add_to_list, set_value
)
from puntini.models.goal_schemas import TodoItem
from puntini.nodes.message import Artifact, Failure


class TestMinimalState:
    """Test cases for MinimalState and related classes."""
    
    def test_minimal_state_creation(self):
        """Test creating a minimal state instance."""
        services = Services(
            tool_registry=Mock(),
            context_manager=Mock(),
            tracer=Mock(),
            graph_store=Mock()
        )
        
        state = MinimalState(
            session_id="test-session",
            current_node="parse_intent",
            shared_services=services,
            goal="Test goal",
            messages=[],
            artifacts=[],
            failures=[],
            progress=[],
            todo_list=[],
            retry_count=0,
            max_retries=3
        )
        
        assert state["session_id"] == "test-session"
        assert state["current_node"] == "parse_intent"
        assert state["goal"] == "Test goal"
        assert state["retry_count"] == 0
        assert state["max_retries"] == 3
    
    def test_services_registry(self):
        """Test Services registry functionality."""
        mock_tool_registry = Mock()
        mock_context_manager = Mock()
        mock_tracer = Mock()
        mock_graph_store = Mock()
        
        services = Services(
            tool_registry=mock_tool_registry,
            context_manager=mock_context_manager,
            tracer=mock_tracer,
            graph_store=mock_graph_store
        )
        
        assert services["tool_registry"] is mock_tool_registry
        assert services["context_manager"] is mock_context_manager
        assert services["tracer"] is mock_tracer
        assert services["graph_store"] is mock_graph_store


class TestNodeInput:
    """Test cases for NodeInput generic class."""
    
    def test_node_input_creation(self):
        """Test creating a NodeInput instance."""
        state = MinimalState(
            session_id="test",
            current_node="test_node",
            shared_services=Services(
                tool_registry=Mock(),
                context_manager=Mock(),
                tracer=Mock(),
                graph_store=Mock()
            ),
            goal="test goal",
            messages=[],
            artifacts=[],
            failures=[],
            progress=[],
            todo_list=[],
            retry_count=0,
            max_retries=3
        )
        
        context = ParseGoalInput(
            raw_goal="Test goal",
            user_context={"user_id": "123"}
        )
        
        node_input = NodeInput(state, context)
        
        assert node_input.state is state
        assert node_input.context is context
        assert node_input.context.raw_goal == "Test goal"
        assert node_input.context.user_context["user_id"] == "123"
    
    def test_create_node_input_function(self):
        """Test the create_node_input helper function."""
        state = MinimalState(
            session_id="test",
            current_node="test_node",
            shared_services=Services(
                tool_registry=Mock(),
                context_manager=Mock(),
                tracer=Mock(),
                graph_store=Mock()
            ),
            goal="test goal",
            messages=[],
            artifacts=[],
            failures=[],
            progress=[],
            todo_list=[],
            retry_count=0,
            max_retries=3
        )
        
        context = PlanStepInput(
            goal_spec=None,
            intent_spec=None,
            current_step_number=1
        )
        
        node_input = create_node_input(state, context)
        
        assert isinstance(node_input, NodeInput)
        assert node_input.state is state
        assert node_input.context is context


class TestNodeContexts:
    """Test cases for node-specific context classes."""
    
    def test_parse_goal_input(self):
        """Test ParseGoalInput context."""
        context = ParseGoalInput(
            raw_goal="Create a new ticket",
            user_context={"user_id": "123", "role": "admin"},
            previous_attempts=["attempt1", "attempt2"]
        )
        
        assert context.raw_goal == "Create a new ticket"
        assert context.user_context["user_id"] == "123"
        assert context.user_context["role"] == "admin"
        assert context.previous_attempts == ["attempt1", "attempt2"]
    
    def test_plan_step_input(self):
        """Test PlanStepInput context."""
        context = PlanStepInput(
            goal_spec=None,
            intent_spec=None,
            graph_snapshot={"nodes": 5, "edges": 10},
            previous_results=[{"step": 1, "result": "success"}],
            current_step_number=2
        )
        
        assert context.current_step_number == 2
        assert context.graph_snapshot["nodes"] == 5
        assert len(context.previous_results) == 1
        assert context.previous_results[0]["step"] == 1
    
    def test_resolve_entities_input(self):
        """Test ResolveEntitiesInput context."""
        intent_spec = Mock()
        context = ResolveEntitiesInput(
            intent_spec=intent_spec,
            graph_context={"similar_entities": ["entity1", "entity2"]},
            entity_candidates=[{"id": "1", "name": "candidate1"}]
        )
        
        assert context.intent_spec is intent_spec
        assert context.graph_context["similar_entities"] == ["entity1", "entity2"]
        assert len(context.entity_candidates) == 1
        assert context.entity_candidates[0]["name"] == "candidate1"
    
    def test_execute_tool_input(self):
        """Test ExecuteToolInput context."""
        context = ExecuteToolInput(
            tool_signature={"tool_name": "create_node", "tool_args": {"label": "User"}},
            validation_result={"valid": True, "errors": []},
            execution_context={"user_id": "123"}
        )
        
        assert context.tool_signature["tool_name"] == "create_node"
        assert context.validation_result["valid"] is True
        assert context.execution_context["user_id"] == "123"
    
    def test_evaluate_input(self):
        """Test EvaluateInput context."""
        context = EvaluateInput(
            execution_result={"status": "success", "result": "node_created"},
            step_plan={"tool": "create_node", "args": {"label": "User"}},
            goal_completion_status=False
        )
        
        assert context.execution_result["status"] == "success"
        assert context.step_plan["tool"] == "create_node"
        assert context.goal_completion_status is False
    
    def test_diagnose_input(self):
        """Test DiagnoseInput context."""
        error_context = Mock()
        failure_history = [Mock(), Mock()]
        
        context = DiagnoseInput(
            error_context=error_context,
            failure_history=failure_history,
            retry_context={"retry_count": 2, "max_retries": 3}
        )
        
        assert context.error_context is error_context
        assert len(context.failure_history) == 2
        assert context.retry_context["retry_count"] == 2
    
    def test_escalate_input(self):
        """Test EscalateInput context."""
        escalation_context = Mock()
        
        context = EscalateInput(
            escalation_context=escalation_context,
            escalation_reason="tool_execution_failed",
            user_input_required=True
        )
        
        assert context.escalation_context is escalation_context
        assert context.escalation_reason == "tool_execution_failed"
        assert context.user_input_required is True
    
    def test_answer_input(self):
        """Test AnswerInput context."""
        context = AnswerInput(
            final_result={"nodes_created": 1, "edges_created": 0},
            summary_context={"total_operations": 1},
            completion_status="success"
        )
        
        assert context.final_result["nodes_created"] == 1
        assert context.summary_context["total_operations"] == 1
        assert context.completion_status == "success"


class TestStateMigration:
    """Test cases for state migration functions."""
    
    def test_extract_minimal_state(self):
        """Test extracting minimal state from bloated state."""
        bloated_state = {
            "session_id": "test-session",
            "current_node": "parse_intent",
            "goal": "Test goal",
            "tool_registry": Mock(),
            "context_manager": Mock(),
            "tracer": Mock(),
            "graph_store": Mock(),
            "messages": [{"role": "user", "content": "test"}],
            "artifacts": [{"type": "node", "id": "1"}],
            "failures": [{"message": "test error"}],
            "progress": ["step 1", "step 2"],
            "todo_list": [{"id": "1", "task": "create node"}],
            "retry_count": 1,
            "max_retries": 3,
            # These should be ignored (node-specific data)
            "parse_goal_response": Mock(),
            "plan_step_response": Mock(),
            "route_tool_response": Mock(),
            "call_tool_response": Mock(),
            "evaluate_response": Mock(),
            "diagnose_response": Mock(),
            "escalate_response": Mock(),
            "answer_response": Mock(),
            "tool_signature": {"tool_name": "test"},
            "error_context": Mock(),
            "escalation_context": Mock()
        }
        
        minimal_state = extract_minimal_state(bloated_state)
        
        assert minimal_state["session_id"] == "test-session"
        assert minimal_state["current_node"] == "parse_intent"
        assert minimal_state["goal"] == "Test goal"
        assert minimal_state["retry_count"] == 1
        assert minimal_state["max_retries"] == 3
        assert len(minimal_state["messages"]) == 1
        assert len(minimal_state["artifacts"]) == 1
        assert len(minimal_state["failures"]) == 1
        assert len(minimal_state["progress"]) == 2
        assert len(minimal_state["todo_list"]) == 1
        
        # Verify services are properly extracted
        assert minimal_state["shared_services"]["tool_registry"] is bloated_state["tool_registry"]
        assert minimal_state["shared_services"]["context_manager"] is bloated_state["context_manager"]
        assert minimal_state["shared_services"]["tracer"] is bloated_state["tracer"]
        assert minimal_state["shared_services"]["graph_store"] is bloated_state["graph_store"]
    
    def test_merge_node_output(self):
        """Test merging node output back into minimal state."""
        services = Services(
            tool_registry=Mock(),
            context_manager=Mock(),
            tracer=Mock(),
            graph_store=Mock()
        )
        
        minimal_state = MinimalState(
            session_id="test",
            current_node="parse_intent",
            shared_services=services,
            goal="test goal",
            messages=[],
            artifacts=[],
            failures=[],
            progress=[],
            todo_list=[],
            retry_count=0,
            max_retries=3
        )
        
        node_output = {
            "progress": ["new progress message"],
            "artifacts": [{"type": "node", "id": "2"}],
            "failures": [{"message": "new error"}],
            "retry_count": 1,
            "result": {"status": "success"}
        }
        
        updated_state = merge_node_output(minimal_state, node_output)
        
        assert updated_state["progress"] == ["new progress message"]
        assert len(updated_state["artifacts"]) == 1
        assert updated_state["artifacts"][0]["id"] == "2"
        assert len(updated_state["failures"]) == 1
        assert updated_state["failures"][0]["message"] == "new error"
        assert updated_state["retry_count"] == 1
        assert updated_state["result"]["status"] == "success"
        
        # Verify original state is not modified
        assert minimal_state["progress"] == []
        assert minimal_state["retry_count"] == 0


class TestSimplifiedState:
    """Test cases for SimplifiedState and related functions."""
    
    def test_create_simplified_state(self):
        """Test creating a simplified state instance."""
        services = Services(
            tool_registry=Mock(),
            context_manager=Mock(),
            tracer=Mock(),
            graph_store=Mock()
        )
        
        state = create_simplified_state(
            session_id="test-session",
            goal="Test goal",
            shared_services=services,
            retry_count=1,
            max_retries=5
        )
        
        assert state["session_id"] == "test-session"
        assert state["goal"] == "Test goal"
        assert state["retry_count"] == 1
        assert state["max_retries"] == 5
        assert state["current_node"] == "start"
        assert state["shared_services"] is services
    
    def test_migrate_from_bloated_state(self):
        """Test migrating from bloated state to simplified state."""
        bloated_state = {
            "session_id": "test-session",
            "current_node": "parse_intent",
            "goal": "Test goal",
            "tool_registry": Mock(),
            "context_manager": Mock(),
            "tracer": Mock(),
            "graph_store": Mock(),
            "messages": [{"role": "user", "content": "test"}],
            "artifacts": [{"type": "node", "id": "1"}],
            "failures": [{"message": "test error"}],
            "progress": ["step 1"],
            "todo_list": [{"id": "1", "task": "create node"}],
            "retry_count": 2,
            "max_retries": 5,
            "result": {"status": "success"},
            "current_step": "parse_intent",
            "current_attempt": 1,
            # Node-specific data that should be ignored
            "parse_goal_response": Mock(),
            "tool_signature": {"tool_name": "test"}
        }
        
        simplified_state = migrate_from_bloated_state(bloated_state)
        
        assert simplified_state["session_id"] == "test-session"
        assert simplified_state["current_node"] == "parse_intent"
        assert simplified_state["goal"] == "Test goal"
        assert simplified_state["retry_count"] == 2
        assert simplified_state["max_retries"] == 5
        assert simplified_state["result"]["status"] == "success"
        assert simplified_state["current_step"] == "parse_intent"
        assert simplified_state["current_attempt"] == 1
        
        # Verify services are properly migrated
        assert simplified_state["shared_services"]["tool_registry"] is bloated_state["tool_registry"]
    
    def test_extract_node_context(self):
        """Test extracting node-specific context from simplified state."""
        services = Services(
            tool_registry=Mock(),
            context_manager=Mock(),
            tracer=Mock(),
            graph_store=Mock()
        )
        
        state = SimplifiedState(
            session_id="test-session",
            current_node="parse_intent",
            shared_services=services,
            goal="Create a new user",
            messages=[],
            artifacts=[],
            failures=[{"message": "previous error", "type": "validation_error"}],
            progress=["step 1", "step 2"],
            todo_list=[{"id": "1", "task": "create user"}],
            retry_count=1,
            max_retries=3,
            result={"status": "success"},
            current_step="parse_intent",
            current_attempt=1
        )
        
        # Test parse_intent context
        context = extract_node_context(state, "parse_intent")
        assert context["session_id"] == "test-session"
        assert context["goal"] == "Create a new user"
        assert context["raw_goal"] == "Create a new user"
        assert len(context["previous_attempts"]) == 1
        assert context["previous_attempts"][0] == "previous error"
        
        # Test plan_step context
        context = extract_node_context(state, "plan_step")
        assert context["current_step_number"] == 3  # len(progress) + 1
        
        # Test evaluate context
        context = extract_node_context(state, "evaluate")
        assert context["execution_result"]["status"] == "success"
        assert context["goal_completion_status"] is False
    
    def test_update_state_with_node_output(self):
        """Test updating state with node output."""
        services = Services(
            tool_registry=Mock(),
            context_manager=Mock(),
            tracer=Mock(),
            graph_store=Mock()
        )
        
        state = SimplifiedState(
            session_id="test-session",
            current_node="parse_intent",
            shared_services=services,
            goal="Test goal",
            messages=[],
            artifacts=[],
            failures=[],
            progress=[],
            todo_list=[],
            retry_count=0,
            max_retries=3,
            result=None,
            current_step="start",
            current_attempt=1
        )
        
        node_output = {
            "progress": ["Parsed intent successfully"],
            "artifacts": [{"type": "intent", "data": {"intent_type": "create"}}],
            "failures": [{"message": "minor warning", "type": "warning"}],
            "result": {"status": "success", "intent_type": "create"},
            "retry_count": 0
        }
        
        updated_state = update_state_with_node_output(state, node_output, "parse_intent")
        
        assert updated_state["current_node"] == "parse_intent"
        assert updated_state["progress"] == ["Parsed intent successfully"]
        assert len(updated_state["artifacts"]) == 1
        assert updated_state["artifacts"][0]["type"] == "intent"
        assert len(updated_state["failures"]) == 1
        assert updated_state["failures"][0]["message"] == "minor warning"
        assert updated_state["result"]["intent_type"] == "create"
        
        # Verify original state is not modified
        assert state["current_node"] == "parse_intent"
        assert state["progress"] == []


class TestReducerFunctions:
    """Test cases for reducer functions."""
    
    def test_add_to_list_reducer(self):
        """Test the add_to_list reducer function."""
        # Test with existing list
        existing = ["item1", "item2"]
        updates = ["item3", "item4"]
        result = add_to_list(existing, updates)
        assert result == ["item1", "item2", "item3", "item4"]
        
        # Test with None existing
        result = add_to_list(None, updates)
        assert result == ["item3", "item4"]
        
        # Test with None updates
        result = add_to_list(existing, None)
        assert result == existing
        
        # Test with both None
        result = add_to_list(None, None)
        assert result == []
    
    def test_set_value_reducer(self):
        """Test the set_value reducer function."""
        # Test normal case
        result = set_value("old_value", "new_value")
        assert result == "new_value"
        
        # Test with None existing
        result = set_value(None, "new_value")
        assert result == "new_value"
        
        # Test with None new value
        result = set_value("old_value", None)
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__])
