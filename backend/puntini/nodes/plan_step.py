"""Plan step node implementation.

This module implements the plan_step node that proposes the next
micro-step and the candidate tool signature using LLM-based planning.
"""

from typing import Any, Dict, List, Optional, TYPE_CHECKING
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime, get_runtime
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from ..orchestration.state_schema import State
from ..llm import LLMFactory
from ..models.goal_schemas import GoalSpec
from ..logging import get_logger
from ..models.errors import ValidationError
from .message import PlanStepResponse, PlanStepResult, Failure




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


def _get_tool_specifications_from_registry(tool_registry) -> str:
    """Generate tool specifications dynamically from the tool registry.
    
    Args:
        tool_registry: Tool registry instance containing available tools.
        
    Returns:
        Formatted string with tool specifications for the LLM prompt.
    """
    if not tool_registry:
        return "No tools available in registry."
    
    tool_specs = []
    tools = tool_registry.list()
    
    for i, tool in enumerate(tools, 1):
        tool_specs.append(f"{i}. {tool.name}: {tool.description}")
        
        # Get input schema if available
        if tool.input_schema and 'properties' in tool.input_schema:
            required_fields = tool.input_schema.get('required', [])
            properties = tool.input_schema['properties']
            
            tool_specs.append("   Required arguments:")
            for field_name, field_info in properties.items():
                is_required = field_name in required_fields
                field_desc = field_info.get('description', 'No description')
                field_type = field_info.get('type', 'unknown')
                required_marker = " (REQUIRED)" if is_required else " (optional)"
                
                tool_specs.append(f"   - {field_name}: {field_desc} (type: {field_type}){required_marker}")
        else:
            tool_specs.append("   No detailed argument information available")
        
        tool_specs.append("")  # Empty line between tools
    
    return "\n".join(tool_specs)


def plan_step(state: "State", config: Optional[RunnableConfig] = None, runtime: Optional[Runtime] = None) -> PlanStepResponse:
    """Plan the next step in the agent's execution using LLM.
    
    This node analyzes the current state, including the parsed goal,
    and determines the next micro-step to take using LLM-based planning
    with structured output for reliable tool selection. The LLM is obtained
    from the graph context instead of creating a new instance.
    
    Args:
        state: Current agent state with parsed goal information.
        config: Optional RunnableConfig for additional configuration.
        runtime: Optional Runtime context for additional runtime information.
        
    Returns:
        Updated state with planned step information.
        
    Notes:
        The planned step includes all necessary information for tool
        execution, including the tool name, validated parameters,
        reasoning, and confidence score.
        The LLM is obtained from the graph context to ensure consistency.
    """
    
    # Initialize logger for this module
    logger = get_logger(__name__)
    
    # Convert state to dict if needed
    if isinstance(state, dict):
        state_dict = state
    else:
        # Convert Pydantic model to dictionary
        state_dict = state.model_dump() if hasattr(state, 'model_dump') else state.__dict__
    
    # Get parsed goal from artifacts
    parsed_goal_data = None
    artifacts = state_dict.get("artifacts", [])
    for artifact in artifacts:
        if artifact.type == "parsed_goal":
            parsed_goal_data = artifact.data
            break
    
    if not parsed_goal_data:
        # Fallback to basic planning without parsed goal
        return _create_fallback_plan(state)
    
    try:
        # Get LLM from graph context
        if runtime is None:

            # Fallback to get_runtime if runtime is not passed directly
            try:
                runtime = get_runtime()
            except Exception as e:
                logger.error(f"Failed to get runtime context: {e}")
                raise ValidationError("Runtime context not available for LLM access")

        # Get the LLM from the context
        if not hasattr(runtime, 'context') or 'llm' not in runtime.context:
            logger.error("LLM not found in runtime context")
            raise ValidationError("LLM not configured in graph context")

        llm : BaseChatModel = runtime.context['llm']

        structured_llm = llm.with_structured_output(StepPlan)
        
        logger.info(
            "Using LLM from graph context for step planning",
            extra={
                "llm_type": type(llm).__name__,
                "target_model": StepPlan.__name__
            }
        )
                   
        # Get tool specifications dynamically from registry
        if isinstance(state, dict):
            tool_registry = state.get("tool_registry")
        else:
            tool_registry = getattr(state, "tool_registry", None)
        tool_specifications = _get_tool_specifications_from_registry(tool_registry)
        
        # Create planning prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""You are an expert at planning graph manipulation steps for an AI agent.

Your task is to analyze the user's goal and plan the next micro-step. You have access to these tools:

{tool_specifications}

Based on the parsed goal information, analyze and plan the next step:
1. Choose the most appropriate tool from the available tools
2. Provide ALL required arguments for the selected tool (ensure all REQUIRED fields are included)
3. Explain your reasoning for choosing this tool and these arguments
4. Assess your confidence in this plan (0.0 to 1.0)
5. Indicate if this is the final step needed to complete the goal

Guidelines:
- ALWAYS include ALL REQUIRED arguments for the selected tool
- Be specific with tool arguments (exact labels, keys, property names)
- Consider the current progress and what's needed next
- Ensure tool arguments are valid and complete
- Provide clear reasoning for your choices
- Be realistic about confidence levels

IMPORTANT: Return a structured StepPlan object, not a tool call. The tool_name should be one of the available tools listed above."""),
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
        progress = state_dict.get("progress", [])
        previous_steps = _get_previous_steps(state_dict)
        
        # Create planning chain
        planning_chain = prompt | structured_llm
        
        # Generate step plan
        step_plan : StepPlan = planning_chain.invoke({
            "goal_info": goal_info,
            "progress": "\n".join(progress) if progress else "No progress yet",
            "previous_steps": previous_steps
        })
        
        # Convert to dictionary for state storage
        planned_step = step_plan.tool_signature.model_dump()
        
        return PlanStepResponse(
            current_step="route_tool",
            tool_signature=planned_step,
            progress=[f"Planned step {step_plan.step_number}: {planned_step['tool_name']}"],
            result=PlanStepResult(
                status="success",
                step_plan=step_plan,  # Pass the StepPlan object directly
                is_final_step=step_plan.is_final_step,
                overall_progress=step_plan.overall_progress
            )
        )
        
    except Exception as e:
        # Handle planning errors gracefully
        error_msg = f"Step planning failed: {str(e)}"
        logger.error("Step planning failed with exception", extra={
            "error_type": type(e).__name__,
            "error_message": str(e)
        })
        
        return PlanStepResponse(
            current_step="diagnose",
            failures=[Failure(step="plan_step", error=error_msg, attempt=1, error_type="planning_error")],
            result=PlanStepResult(
                status="error",
                error=error_msg,
                error_type="planning_error"
            )
        )


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


def _get_previous_steps(state: dict) -> str:
    """Get information about previous steps from state.
    
    Args:
        state: Current agent state dictionary.
        
    Returns:
        String describing previous steps.
    """
    progress = state.get("progress", [])
    if not progress:
        return "No previous steps"
    
    # Get last few progress items
    recent_progress = progress[-3:] if len(progress) > 3 else progress
    return "\n".join(recent_progress)


def _create_fallback_plan(state: "State") -> PlanStepResponse:
    """Create a fallback plan when goal parsing is not available.
    
    Args:
        state: Current agent state.
        
    Returns:
        Basic fallback plan.
    """
    # Convert state to dict if needed
    if isinstance(state, dict):
        state_dict = state
    else:
        # Convert Pydantic model to dictionary
        state_dict = state.model_dump() if hasattr(state, 'model_dump') else state.__dict__
    
    goal = state_dict.get("goal", "Unknown goal")
    
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
    
    # Create a proper StepPlan object for fallback
    fallback_step_plan = StepPlan(
        step_number=1,
        tool_signature=ToolSignature(
            tool_name=planned_step["tool_name"],
            tool_args=planned_step["tool_args"],
            reasoning=planned_step["reasoning"],
            confidence=planned_step["confidence"],
            expected_outcome=planned_step["expected_outcome"]
        ),
        is_final_step=False,
        next_step_hint="Analyze results and plan next action",
        overall_progress=0.1
    )
    
    return PlanStepResponse(
        current_step="route_tool",
        tool_signature=planned_step,
        progress=[f"Fallback planned step: {planned_step['tool_name']}"],
        result=PlanStepResult(
            status="success",
            step_plan=fallback_step_plan,  # Pass the StepPlan object directly
            is_final_step=False,
            overall_progress=0.1
        )
    )
