#!/usr/bin/env python3
"""Standalone test for streamlined message architecture."""

import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

# Import directly from the file without triggering full package import
# We'll bypass the package system to avoid circular imports
from puntini.backend.puntini.nodes.streamlined_message import (
    GenericNodeResponse,
    ParseGoalResult,
    PlanStepResult,
    ExecuteToolResult,
    EvaluateResult,
    DiagnoseResult,
    AnswerResult,
    EscalateResult,
    Artifact,
    Failure,
    ErrorContext,
    EscalateContext
)

def test_streamlined_architecture():
    """Test the streamlined message architecture."""
    print("Testing streamlined message architecture...")
    
    # Test ParseGoalResult
    parse_result = ParseGoalResult(
        status="success",
        parsed_goal={"intent": "create_ticket"},
        complexity="simple"
    )
    
    print(f"ParseGoalResult created: {parse_result}")
    print(f"Status: {parse_result.status}")
    print(f"Parsed goal: {parse_result.parsed_goal}")
    
    # Test GenericNodeResponse wrapper
    parse_response = GenericNodeResponse[ParseGoalResult](
        current_step="plan_step",
        progress=["Parsed goal successfully"],
        artifacts=[Artifact(type="parsed_goal", data={"intent": "create_ticket"})],
        result=parse_result
    )
    
    print(f"\nGenericNodeResponse created: {parse_response}")
    print(f"Current step: {parse_response.current_step}")
    print(f"Progress: {parse_response.progress}")
    print(f"Artifacts count: {len(parse_response.artifacts)}")
    
    # Test ExecuteToolResult
    tool_result = ExecuteToolResult(
        status="success",
        tool_name="create_ticket",
        result={"ticket_id": "TICKET-123"},
        execution_time=0.5
    )
    
    print(f"\nExecuteToolResult created: {tool_result}")
    print(f"Tool name: {tool_result.tool_name}")
    print(f"Result: {tool_result.result}")
    
    # Test GenericNodeResponse wrapper with ExecuteToolResult
    tool_response = GenericNodeResponse[ExecuteToolResult](
        current_step="evaluate",
        progress=["Executed tool successfully"],
        artifacts=[Artifact(type="tool_execution", data={"tool_name": "create_ticket", "execution_time": 0.5})],
        result=tool_result
    )
    
    print(f"\nGenericNodeResponse with ExecuteToolResult created: {tool_response}")
    print(f"Current step: {tool_response.current_step}")
    print(f"Execution result: {tool_response.result.result}")
    
    print("\nAll tests passed!")

if __name__ == "__main__":
    test_streamlined_architecture()