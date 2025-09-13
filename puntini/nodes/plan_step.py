"""Plan step node implementation.

This module implements the plan_step node that proposes the next
micro-step and the candidate tool signature using LLM-based planning.
"""

from typing import Any, Dict, List
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from ..orchestration.state import State
from ..llm import LLMFactory
from ..models.goal_schemas import GoalSpec


class ToolSignature(BaseModel):
    """Schema for tool signature in step planning."""
    tool_name: str = Field(description="The name of the tool to execute")
    tool_args: Dict[str, Any] = Field(description="Arguments for the tool")
    reasoning: str = Field(description="Reasoning for choosing this tool and arguments")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score for this plan")
    expected_outcome: str = Field(description="Expected outcome of executing this tool")


class StepPlan(BaseModel):
    """Schema for step planning output."""
    step_number: int = Field(description="The step number in the overall plan")
    tool_signature: ToolSignature = Field(description="The tool signature for this step")
    is_final_step: bool = Field(description="Whether this is the final step in the plan")
    next_step_hint: str = Field(description="Hint for the next step if not final")
    overall_progress: float = Field(ge=0.0, le=1.0, description="Overall progress towards goal completion")


def plan_step(state: State) -> Dict[str, Any]:
    """Plan the next step in the agent's execution using LLM.
    
    This node analyzes the current state, including the parsed goal,
    and determines the next micro-step to take using LLM-based planning
    with structured output for reliable tool selection.
    
    Args:
        state: Current agent state with parsed goal information.
        
    Returns:
        Updated state with planned step information.
        
    Notes:
        The planned step includes all necessary information for tool
        execution, including the tool name, validated parameters,
        reasoning, and confidence score.
    """
    # Get parsed goal from artifacts
    parsed_goal_data = None
    for artifact in state.get("artifacts", []):
        if artifact.get("type") == "parsed_goal":
            parsed_goal_data = artifact.get("data")
            break
    
    if not parsed_goal_data:
        # Fallback to basic planning without parsed goal
        return _create_fallback_plan(state)
    
    try:
        # Get LLM from factory
        llm_factory = LLMFactory()
        llm = llm_factory.create_structured_llm("openai-gpt4", StepPlan)
        
        # Create planning prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at planning graph manipulation steps for an AI agent.

Your task is to plan the next micro-step to achieve the user's goal. You have access to these tools:
- add_node: Create a new node with label, key, and properties
- add_edge: Create a relationship between two nodes
- update_props: Update properties of existing nodes or edges
- delete_node: Remove a node and its relationships
- delete_edge: Remove a relationship
- query_graph: Search and retrieve graph data
- cypher_query: Execute custom Cypher queries

Based on the parsed goal information, plan the next step:
1. Choose the most appropriate tool
2. Provide valid arguments for the tool
3. Explain your reasoning
4. Assess your confidence in this plan
5. Indicate if this is the final step

Guidelines:
- Be specific with tool arguments (exact labels, keys, property names)
- Consider the current progress and what's needed next
- Ensure tool arguments are valid and complete
- Provide clear reasoning for your choices
- Be realistic about confidence levels

Return a StepPlan object with your analysis."""),
            ("human", """Parsed Goal Information:
{goal_info}

Current Progress:
{progress}

Previous Steps:
{previous_steps}

Plan the next step to move towards achieving this goal.""")
        ])
        
        # Prepare context for planning
        goal_info = _format_goal_info(parsed_goal_data)
        progress = state.get("progress", [])
        previous_steps = _get_previous_steps(state)
        
        # Create planning chain
        planning_chain = prompt | llm
        
        # Generate step plan
        step_plan = planning_chain.invoke({
            "goal_info": goal_info,
            "progress": "\n".join(progress) if progress else "No progress yet",
            "previous_steps": previous_steps
        })
        
        # Convert to dictionary for state storage
        planned_step = step_plan.tool_signature.model_dump()
        
        return {
            "current_step": "route_tool",
            "_tool_signature": planned_step,
            "progress": [f"Planned step {step_plan.step_number}: {planned_step['tool_name']}"],
            "result": {
                "status": "success",
                "step_plan": step_plan.model_dump(),
                "is_final_step": step_plan.is_final_step,
                "overall_progress": step_plan.overall_progress
            }
        }
        
    except Exception as e:
        # Handle planning errors gracefully
        error_msg = f"Step planning failed: {str(e)}"
        
        return {
            "current_step": "diagnose",
            "failures": [{"step": "plan_step", "error": error_msg, "attempt": 1}],
            "result": {
                "status": "error",
                "error": error_msg,
                "error_type": "planning_error"
            }
        }


def _format_goal_info(parsed_goal_data: Dict[str, Any]) -> str:
    """Format parsed goal data for LLM planning.
    
    Args:
        parsed_goal_data: Dictionary containing parsed goal information.
        
    Returns:
        Formatted string with goal information.
    """
    lines = [
        f"Intent: {parsed_goal_data.get('intent', 'N/A')}",
        f"Complexity: {parsed_goal_data.get('complexity', 'N/A')}",
        f"Estimated Steps: {parsed_goal_data.get('estimated_steps', 'N/A')}"
    ]
    
    # Add entities
    entities = parsed_goal_data.get('entities', [])
    if entities:
        lines.append("\nEntities:")
        for entity in entities:
            lines.append(f"  - {entity.get('name', 'N/A')} ({entity.get('type', 'N/A')})")
            if entity.get('label'):
                lines.append(f"    Label: {entity['label']}")
            if entity.get('properties'):
                lines.append(f"    Properties: {entity['properties']}")
    
    # Add constraints
    constraints = parsed_goal_data.get('constraints', [])
    if constraints:
        lines.append("\nConstraints:")
        for constraint in constraints:
            lines.append(f"  - {constraint.get('type', 'N/A')}: {constraint.get('description', 'N/A')}")
    
    # Add domain hints
    domain_hints = parsed_goal_data.get('domain_hints', [])
    if domain_hints:
        lines.append("\nDomain Context:")
        for hint in domain_hints:
            lines.append(f"  - {hint.get('domain', 'N/A')}: {hint.get('hint', 'N/A')}")
    
    return "\n".join(lines)


def _get_previous_steps(state: State) -> str:
    """Get information about previous steps from state.
    
    Args:
        state: Current agent state.
        
    Returns:
        String describing previous steps.
    """
    progress = state.get("progress", [])
    if not progress:
        return "No previous steps"
    
    # Get last few progress items
    recent_progress = progress[-3:] if len(progress) > 3 else progress
    return "\n".join(recent_progress)


def _create_fallback_plan(state: State) -> Dict[str, Any]:
    """Create a fallback plan when goal parsing is not available.
    
    Args:
        state: Current agent state.
        
    Returns:
        Basic fallback plan.
    """
    goal = state.get("goal", "unknown goal")
    
    # Simple fallback planning based on goal text
    planned_step = {
        "tool_name": "query_graph",
        "tool_args": {
            "query": "MATCH (n) RETURN n LIMIT 10"
        },
        "reasoning": f"Fallback plan: querying graph to understand current state for goal: {goal}",
        "confidence": 0.3,
        "expected_outcome": "Understanding of current graph state"
    }
    
    return {
        "current_step": "route_tool",
        "_tool_signature": planned_step,
        "progress": [f"Fallback planned step: {planned_step['tool_name']}"],
        "result": {
            "status": "success",
            "step_plan": {
                "step_number": 1,
                "tool_signature": planned_step,
                "is_final_step": False,
                "next_step_hint": "Analyze results and plan next action",
                "overall_progress": 0.1
            },
            "is_final_step": False,
            "overall_progress": 0.1
        }
    }
