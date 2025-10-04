"""Unit tests for streamlined response architecture.

This module tests the streamlined response architecture implemented in Phase 6
of the progressive refactoring plan, ensuring that the generic response wrapper
with node-specific result types eliminates redundant response patterns as specified.
"""

import pytest
from datetime import datetime
from typing import Dict, Any, List

from puntini.nodes.streamlined_message import (
    GenericNodeResponse,
    ParseGoalResult,
    PlanStepResult,
    ExecuteToolResult,
    EvaluateResult,
    DiagnoseResult,
    AnswerResult,
    EscalateResult,
    EscalateContext,
    Artifact,
    Failure,
    ErrorContext
)


class TestStreamlinedMessageArchitecture:
    """Test the streamlined message architecture components."""
    
    def test_generic_node_response_wrapper(self):
        """Test the generic node response wrapper with different result types."""
        # Test with ParseGoalResult
        parse_result = ParseGoalResult(
            status="success",
            parsed_goal={"intent": "create_ticket"},
            complexity="simple"
        )
        
        parse_response = GenericNodeResponse[ParseGoalResult](
            current_step="plan_step",
            progress=["Parsed goal successfully"],
            artifacts=[Artifact(type="parsed_goal", data={"intent": "create_ticket"})],
            result=parse_result
        )
        
        assert parse_response.current_step == "plan_step"
        assert len(parse_response.progress) == 1
        assert len(parse_response.artifacts) == 1
        assert parse_response.result.status == "success"
        assert parse_response.result.parsed_goal == {"intent": "create_ticket"}
        
        # Test with ExecuteToolResult
        tool_result = ExecuteToolResult(
            status="success",
            tool_name="create_ticket",
            result={"ticket_id": "TICKET-123"},
            execution_time=0.5
        )
        
        tool_response = GenericNodeResponse[ExecuteToolResult](
            current_step="evaluate",
            progress=["Executed tool successfully"],
            artifacts=[Artifact(type="tool_execution", data={"tool_name": "create_ticket", "execution_time": 0.5})],
            result=tool_result
        )
        
        assert tool_response.current_step == "evaluate"
        assert tool_response.result.status == "success"
        assert tool_response.result.tool_name == "create_ticket"
        assert tool_response.result.result == {"ticket_id": "TICKET-123"}
    
    def test_parse_goal_result_fields(self):
        """Test ParseGoalResult has all expected fields."""
        result = ParseGoalResult(
            status="success",
            parsed_goal={"intent": "create_user", "entities": ["John Doe"]},
            complexity="medium",
            requires_graph_ops=True,
            is_simple=False
        )
        
        assert result.status == "success"
        assert result.parsed_goal == {"intent": "create_user", "entities": ["John Doe"]}
        assert result.complexity == "medium"
        assert result.requires_graph_ops is True
        assert result.is_simple is False
    
    def test_plan_step_result_fields(self):
        """Test PlanStepResult has all expected fields."""
        result = PlanStepResult(
            status="success",
            step_plan={"action": "create_node", "entity": "User"},
            is_final_step=False,
            overall_progress=0.5
        )
        
        assert result.status == "success"
        assert result.step_plan == {"action": "create_node", "entity": "User"}
        assert result.is_final_step is False
        assert result.overall_progress == 0.5
    
    def test_execute_tool_result_fields(self):
        """Test ExecuteToolResult has all expected fields."""
        result = ExecuteToolResult(
            status="success",
            tool_name="add_node",
            result={"node_id": "user:123"},
            result_type="add_node",
            routing_decision={"selected_tool": "add_node"},
            execution_time=0.75
        )
        
        assert result.status == "success"
        assert result.tool_name == "add_node"
        assert result.result == {"node_id": "user:123"}
        assert result.result_type == "add_node"
        assert result.routing_decision == {"selected_tool": "add_node"}
        assert result.execution_time == 0.75
    
    def test_evaluate_result_fields(self):
        """Test EvaluateResult has all expected fields."""
        result = EvaluateResult(
            status="success",
            retry_count=1,
            max_retries=3,
            evaluation_timestamp="2025-01-01T12:00:00Z",
            decision_reason="Goal progressing well",
            goal_complete=False,
            next_action="continue_planning"
        )
        
        assert result.status == "success"
        assert result.retry_count == 1
        assert result.max_retries == 3
        assert result.evaluation_timestamp == "2025-01-01T12:00:00Z"
        assert result.decision_reason == "Goal progressing well"
        assert result.goal_complete is False
        assert result.next_action == "continue_planning"
    
    def test_diagnose_result_fields(self):
        """Test DiagnoseResult has all expected fields."""
        result = DiagnoseResult(
            status="success",
            error_classification="validation_error",
            remediation_strategy="correct_invalid_arguments",
            confidence=0.85,
            recommended_action="replan_with_corrected_args"
        )
        
        assert result.status == "success"
        assert result.error_classification == "validation_error"
        assert result.remediation_strategy == "correct_invalid_arguments"
        assert result.confidence == 0.85
        assert result.recommended_action == "replan_with_corrected_args"
    
    def test_answer_result_fields(self):
        """Test AnswerResult has all expected fields."""
        result = AnswerResult(
            status="success",
            summary="Successfully created user and assigned to project",
            steps_taken=5,
            artifacts_created=3,
            final_result={"user_id": "user:123", "project_id": "proj:456"}
        )
        
        assert result.status == "success"
        assert result.summary == "Successfully created user and assigned to project"
        assert result.steps_taken == 5
        assert result.artifacts_created == 3
        assert result.final_result == {"user_id": "user:123", "project_id": "proj:456"}
    
    def test_escalate_result_fields(self):
        """Test EscalateResult has all expected fields."""
        result = EscalateResult(
            status="success"
        )
        
        assert result.status == "success"
    
    def test_artifact_model(self):
        """Test Artifact model has correct fields."""
        artifact = Artifact(
            type="tool_execution",
            data={"tool_name": "add_node", "execution_time": 0.5}
        )
        
        assert artifact.type == "tool_execution"
        assert artifact.data == {"tool_name": "add_node", "execution_time": 0.5}
    
    def test_failure_model(self):
        """Test Failure model has correct fields."""
        failure = Failure(
            step="execute_tool",
            error="Timeout error",
            attempt=2,
            error_type="network_error",
            timestamp=datetime.utcnow()
        )
        
        assert failure.step == "execute_tool"
        assert failure.error == "Timeout error"
        assert failure.attempt == 2
        assert failure.error_type == "network_error
    
    def test_error_context_model(self):
        """Test ErrorContext model has correct fields."""
        error_context = ErrorContext(
            type="validation_error",
            message="Invalid arguments provided",
            details={"field": "email", "expected_format": "email_address"}
        )
        
        assert error_context.type == "validation_error"
        assert error_context.message == "Invalid arguments provided"
        assert error_context.details == {"field": "email", "expected_format": "email_address"}
    
    def test_escalate_context_model(self):
        """Test EscalateContext model has correct fields."""
        escalate_context = EscalateContext(
            reason="Ambiguous entity reference",
            error="Multiple entities match 'John'",
            options=["John Doe (user:123)", "John Smith (user:456)"],
            recommended_action="Ask user to clarify which John"
        )
        
        assert escalate_context.reason == "Ambiguous entity reference"
        assert escalate_context.error == "Multiple entities match 'John'"
        assert escalate_context.options == ["John Doe (user:123)", "John Smith (user:456)"]
        assert escalate_context.recommended_action == "Ask user to clarify which John"
    
    def test_backward_compatibility_union_types(self):
        """Test that union types work with different response types."""
        # Test ParseGoalResponse
        parse_result = ParseGoalResult(status="success", parsed_goal={"intent": "create_ticket"})
        parse_response = GenericNodeResponse[ParseGoalResult](
            current_step="plan_step",
            result=parse_result
        )
        
        # Test ExecuteToolResponse
        tool_result = ExecuteToolResult(status="success", tool_name="create_ticket")
        tool_response = GenericNodeResponse[ExecuteToolResult](
            current_step="evaluate",
            result=tool_result
        )
        
        # Both should be valid GenericNodeResponse instances
        assert isinstance(parse_response, GenericNodeResponse)
        assert isinstance(tool_response, GenericNodeResponse)
        
        # Test that they have the correct result types
        assert isinstance(parse_response.result, ParseGoalResult)
        assert isinstance(tool_response.result, ExecuteToolResult)