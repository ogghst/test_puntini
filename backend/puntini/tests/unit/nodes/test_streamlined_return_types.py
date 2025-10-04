"""Unit tests for streamlined return types.

This module tests the streamlined return types implemented in Phase 6
of the progressive refactoring plan, ensuring that the generic return types
with node-specific result types eliminate redundant response patterns as specified.
"""

import pytest
from typing import Dict, Any, List

from puntini.nodes.streamlined_return_types import (
    ParseGoalReturn,
    PlanStepReturn,
    ExecuteToolReturn,
    EvaluateReturn,
    DiagnoseReturn,
    AnswerReturn,
    EscalateReturn,
    CommandReturn,
    EvaluateCommandReturn,
    EscalateCommandReturn,
    Artifact,
    Failure,
    ErrorContext,
    EscalateContext
)

from puntini.nodes.streamlined_message import (
    ParseGoalResult,
    PlanStepResult,
    ExecuteToolResult,
    EvaluateResult,
    DiagnoseResult,
    AnswerResult,
    EscalateResult
)


class TestStreamlinedReturnTypes:
    """Test the streamlined return types architecture."""
    
    def test_generic_node_return_wrapper(self):
        """Test the generic node return wrapper with different result types."""
        # Test with ParseGoalResult
        parse_result = ParseGoalResult(
            status="success",
            parsed_goal={"intent": "create_ticket"},
            complexity="simple"
        )
        
        parse_return = ParseGoalReturn(
            current_step="plan_step",
            progress=["Parsed goal successfully"],
            artifacts=[Artifact(type="parsed_goal", data={"intent": "create_ticket"})],
            node_result=parse_result,
            current_attempt=1
        )
        
        assert parse_return.current_step == "plan_step"
        assert len(parse_return.progress) == 1
        assert len(parse_return.artifacts) == 1
        assert parse_return.node_result.status == "success"
        assert parse_return.node_result.parsed_goal == {"intent": "create_ticket"}
        assert parse_return.current_attempt == 1
    
    def test_parse_goal_return_fields(self):
        """Test ParseGoalReturn has all expected fields."""
        parse_result = ParseGoalResult(
            status="success",
            parsed_goal={"intent": "create_user", "entities": ["John Doe"]},
            complexity="medium",
            requires_graph_ops=True,
            is_simple=False
        )
        
        parse_return = ParseGoalReturn(
            current_step="plan_step",
            progress=["Goal parsing completed"],
            artifacts=[],
            failures=[],
            node_result=parse_result,
            current_attempt=1,
            parse_goal_response={"some": "metadata"}
        )
        
        assert parse_return.current_step == "plan_step"
        assert parse_return.current_attempt == 1
        assert parse_return.parse_goal_response == {"some": "metadata"}
        assert parse_return.node_result.status == "success"
    
    def test_plan_step_return_fields(self):
        """Test PlanStepReturn has all expected fields."""
        plan_result = PlanStepResult(
            status="success",
            step_plan={"action": "create_node", "entity": "User"},
            is_final_step=False,
            overall_progress=0.5
        )
        
        plan_return = PlanStepReturn(
            current_step="execute_tool",
            progress=["Plan step completed"],
            artifacts=[],
            failures=[],
            node_result=plan_result,
            plan_step_response={"step_id": "step_1"},
            tool_signature={"tool_name": "add_node"}
        )
        
        assert plan_return.current_step == "execute_tool"
        assert plan_return.plan_step_response == {"step_id": "step_1"}
        assert plan_return.tool_signature == {"tool_name": "add_node"}
        assert plan_return.node_result.status == "success"
    
    def test_execute_tool_return_fields(self):
        """Test ExecuteToolReturn has all expected fields."""
        tool_result = ExecuteToolResult(
            status="success",
            tool_name="add_node",
            result={"node_id": "user:123"},
            result_type="add_node",
            routing_decision={"selected_tool": "add_node"},
            execution_time=0.75
        )
        
        tool_return = ExecuteToolReturn(
            current_step="evaluate",
            progress=["Tool execution completed"],
            artifacts=[],
            failures=[],
            node_result=tool_result,
            execute_tool_response={"execution_id": "exec_1"},
            tool_signature={"tool_name": "add_node", "tool_args": {"label": "User"}}
        )
        
        assert tool_return.current_step == "evaluate"
        assert tool_return.execute_tool_response == {"execution_id": "exec_1"}
        assert tool_return.tool_signature == {"tool_name": "add_node", "tool_args": {"label": "User"}}
        assert tool_return.node_result.status == "success"
    
    def test_evaluate_return_fields(self):
        """Test EvaluateReturn has all expected fields."""
        eval_result = EvaluateResult(
            status="success",
            retry_count=1,
            max_retries=3,
            evaluation_timestamp="2025-01-01T12:00:00Z",
            decision_reason="Goal progressing well",
            goal_complete=False,
            next_action="continue_planning"
        )
        
        eval_return = EvaluateReturn(
            current_step="plan_step",
            progress=["Evaluation completed"],
            artifacts=[],
            failures=[],
            node_result=eval_result,
            evaluate_response={"evaluation_id": "eval_1"},
            todo_list=[{"task": "Continue planning", "completed": False}]
        )
        
        assert eval_return.current_step == "plan_step"
        assert eval_return.evaluate_response == {"evaluation_id": "eval_1"}
        assert len(eval_return.todo_list) == 1
        assert eval_return.node_result.status == "success"
    
    def test_diagnose_return_fields(self):
        """Test DiagnoseReturn has all expected fields."""
        diag_result = DiagnoseResult(
            status="success",
            error_classification="validation_error",
            remediation_strategy="correct_invalid_arguments",
            confidence=0.85,
            recommended_action="replan_with_corrected_args"
        )
        
        diag_return = DiagnoseReturn(
            current_step="plan_step",
            progress=["Diagnosis completed"],
            artifacts=[],
            failures=[],
            node_result=diag_result,
            diagnose_response={"diagnosis_id": "diag_1"},
            error_context=ErrorContext(
                type="validation_error",
                message="Invalid arguments provided",
                details={"field": "email"}
            )
        )
        
        assert diag_return.current_step == "plan_step"
        assert diag_return.diagnose_response == {"diagnosis_id": "diag_1"}
        assert diag_return.error_context.type == "validation_error"
        assert diag_return.node_result.status == "success"
    
    def test_answer_return_fields(self):
        """Test AnswerReturn has all expected fields."""
        answer_result = AnswerResult(
            status="success",
            summary="Successfully created user and assigned to project",
            steps_taken=5,
            artifacts_created=3,
            final_result={"user_id": "user:123", "project_id": "proj:456"}
        )
        
        answer_return = AnswerReturn(
            current_step="END",
            progress=["Task completed"],
            artifacts=[],
            failures=[],
            node_result=answer_result,
            answer_response={"answer_id": "ans_1"}
        )
        
        assert answer_return.current_step == "END"
        assert answer_return.answer_response == {"answer_id": "ans_1"}
        assert answer_return.node_result.status == "success"
    
    def test_escalate_return_fields(self):
        """Test EscalateReturn has all expected fields."""
        escalate_result = EscalateResult(
            status="success"
        )
        
        escalate_return = EscalateReturn(
            current_step="HUMAN_INPUT",
            progress=["Escalation initiated"],
            artifacts=[],
            failures=[],
            node_result=escalate_result,
            escalate_response={"escalation_id": "esc_1"},
            escalation_context=EscalateContext(
                reason="Ambiguous entity reference",
                error="Multiple entities match 'John'",
                options=["John Doe (user:123)", "John Smith (user:456)"],
                recommended_action="Ask user to clarify which John"
            )
        )
        
        assert escalate_return.current_step == "HUMAN_INPUT"
        assert escalate_return.escalate_response == {"escalation_id": "esc_1"}
        assert escalate_return.escalation_context.reason == "Ambiguous entity reference"
        assert escalate_return.node_result.status == "success"
    
    def test_command_return_types(self):
        """Test Command return types."""
        # Test basic CommandReturn
        command_return = CommandReturn(
            update={"current_step": "plan_step"},
            goto="plan_step",
            resume="user_input"
        )
        
        assert command_return.update == {"current_step": "plan_step"}
        assert command_return.goto == "plan_step"
        assert command_return.resume == "user_input"
        
        # Test EvaluateCommandReturn
        eval_command_return = EvaluateCommandReturn(
            update={"current_step": "plan_step"},
            goto="plan_step",
            evaluate_response={"result": "success"}
        )
        
        assert eval_command_return.update == {"current_step": "plan_step"}
        assert eval_command_return.goto == "plan_step"
        assert eval_command_return.evaluate_response == {"result": "success"}
        
        # Test EscalateCommandReturn
        escalate_command_return = EscalateCommandReturn(
            update={"current_step": "diagnose"},
            goto="diagnose",
            escalate_response={"error": "Ambiguous entity"},
            escalation_context=EscalateContext(
                reason="Ambiguous entity reference",
                error="Multiple entities match 'John'",
                options=["John Doe (user:123)", "John Smith (user:456)"],
                recommended_action="Ask user to clarify which John"
            )
        )
        
        assert escalate_command_return.update == {"current_step": "diagnose"}
        assert escalate_command_return.goto == "diagnose"
        assert escalate_command_return.escalate_response == {"error": "Ambiguous entity"}
        assert escalate_command_return.escalation_context.reason == "Ambiguous entity reference"
    
    def test_state_update_conversion(self):
        """Test conversion to state update dictionaries."""
        parse_result = ParseGoalResult(
            status="success",
            parsed_goal={"intent": "create_user"},
            complexity="simple"
        )
        
        parse_return = ParseGoalReturn(
            current_step="plan_step",
            progress=["Goal parsed"],
            artifacts=[Artifact(type="parsed_goal", data={"intent": "create_user"})],
            failures=[],
            node_result=parse_result,
            current_attempt=1,
            parse_goal_response={"intent": "create_user"}
        )
        
        state_update = parse_return.to_state_update()
        
        assert state_update["current_step"] == "plan_step"
        assert "Goal parsed" in state_update["progress"]
        assert len(state_update["artifacts"]) == 1
        assert state_update["node_result"].status == "success"
        assert state_update["current_attempt"] == 1
        assert state_update["parse_goal_response"] == {"intent": "create_user"}
    
    def test_backward_compatibility_union_types(self):
        """Test that union types work with different return types."""
        # Test ParseGoalReturn
        parse_result = ParseGoalResult(status="success", parsed_goal={"intent": "create_ticket"})
        parse_return = ParseGoalReturn(
            current_step="plan_step",
            progress=["Parsed goal successfully"],
            artifacts=[],
            failures=[],
            node_result=parse_result
        )
        
        # Test ExecuteToolReturn
        tool_result = ExecuteToolResult(status="success", tool_name="create_ticket")
        tool_return = ExecuteToolReturn(
            current_step="evaluate",
            progress=["Tool executed successfully"],
            artifacts=[],
            failures=[],
            node_result=tool_result
        )
        
        # Both should be instances of their respective return types
        assert isinstance(parse_return, ParseGoalReturn)
        assert isinstance(tool_return, ExecuteToolReturn)
        
        # Test that they have the correct result types
        assert isinstance(parse_return.node_result, ParseGoalResult)
        assert isinstance(tool_return.node_result, ExecuteToolResult)