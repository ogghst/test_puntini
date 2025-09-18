"""Parse goal node implementation.

This module implements the parse_goal node that extracts goal,
constraints, and domain hints as structured data using LangChain
and Pydantic models for robust parsing and validation.
"""

from typing import Any, Dict, Optional, TYPE_CHECKING
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime, get_runtime
from langchain_core.language_models.chat_models import BaseChatModel

if TYPE_CHECKING:
    from ..orchestration.state_schema import State
from ..models.goal_schemas import GoalSpec, GoalComplexity
from ..models.errors import ValidationError
from ..logging import get_logger
from .message import ParseGoalResponse, ParseGoalResult, Artifact, Failure, ErrorContext


def parse_goal(state: "State", config: Optional[RunnableConfig] = None, runtime: Optional[Runtime] = None) -> ParseGoalResponse:
    """Parse the goal and extract structured information using LLM.
    
    This node extracts the goal, constraints, and domain hints from
    the input using LangChain's structured output capabilities and
    Pydantic models for validation. The LLM is obtained from the
    graph context instead of creating a new instance.
    
    Args:
        state: Current agent state containing the goal.
        config: Optional RunnableConfig for additional configuration.
        runtime: Optional Runtime context for additional runtime information.
        
    Returns:
        Updated state with parsed goal information.
        
    Raises:
        ValidationError: If the goal cannot be parsed or validated.
        
    Notes:
        This is the first node in the execution flow and should
        extract all necessary information from the input goal.
        Uses progressive context disclosure - attempt 1 with minimal context.
        The LLM is obtained from the graph context to ensure consistency.
    """
    # Initialize logger for this module
    logger = get_logger(__name__)
    
    # Validate state input and convert to dict if needed
    logger.debug(f"State type: {type(state)}, State value: {state}")
    if isinstance(state, dict):
        state_dict = state
    else:
        # Convert Pydantic model to dictionary
        state_dict = state.model_dump() if hasattr(state, 'model_dump') else state.__dict__
    
    goal = state_dict.get("goal")
    current_attempt = state_dict.get("current_attempt", 1)
    
    # Validate required fields
    if not isinstance(goal, str):
        raise ValidationError("Goal must be a string")
    
    if not isinstance(current_attempt, int) or current_attempt < 1:
        raise ValidationError("Current attempt must be a positive integer")
    
    # Log function entry with context
    logger.info(
        "Starting goal parsing",
        extra={
            "goal_length": len(goal),
            "current_attempt": current_attempt,
            "state_type": type(state).__name__
        }
    )
    
    if not goal.strip():
        logger.error("Empty goal provided", extra={"goal": goal})
        raise ValidationError("Goal cannot be empty")
    
    try:
        # Get LLM from graph context
        logger.debug("Getting LLM from graph context for goal parsing")
        
        # Get the runtime context to access the configured LLM
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
      
        # Create structured LLM for goal parsing
        structured_llm = llm.with_structured_output(GoalSpec)
        
        logger.info(
            "Using LLM from graph context for goal parsing",
            extra={
                "llm_type": type(llm).__name__,
                "target_model": GoalSpec.__name__
            }
        )
        
        # Create prompt for goal parsing (progressive disclosure - attempt 1)
        logger.debug("Creating parsing prompt template")
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at parsing natural language goals for a graph manipulation agent.

Your task is to extract structured information from user goals that involve graph operations like:
- Creating nodes (entities with labels and properties)
- Creating edges (relationships between entities)
- Updating properties
- Querying the graph
- Complex multi-step operations

For each goal, extract:
1. ENTITIES: Any nodes, edges, or properties mentioned
2. CONSTRAINTS: Any requirements, rules, or limitations
3. DOMAIN_HINTS: Context clues about the domain (project management, social network, etc.)
4. COMPLEXITY: Assess how complex the goal is (simple/medium/complex)
5. INTENT: The primary purpose or objective

Guidelines:
- Be precise in entity extraction - identify names, labels, and properties
- Recognize relationship types and directions
- Identify implicit constraints (uniqueness, required properties, etc.)
- Extract domain context that might help with execution
- Be conservative with complexity assessment
- Focus on actionable, structured information

Return a GoalSpec object with all extracted information."""),
            ("human", "Parse this goal: {goal}")
        ])
        
        # Create the parsing chain
        logger.debug("Creating parsing chain")
        parsing_chain = prompt | structured_llm
        
        # Parse the goal
        logger.info("Invoking LLM for goal parsing", extra={"goal_preview": goal[:100] + "..." if len(goal) > 100 else goal})
        parsed_goal_spec = parsing_chain.invoke({"goal": goal})
        
        logger.info(
            "Successfully parsed goal",
            extra={
                "parsed_entities": len(parsed_goal_spec.entities) if parsed_goal_spec.entities else 0,
                "complexity": parsed_goal_spec.complexity.value if parsed_goal_spec.complexity else None,
                "intent_length": len(parsed_goal_spec.intent) if parsed_goal_spec.intent else 0
            }
        )
        
        # Validate the parsed goal
        logger.debug("Validating parsed goal specification")
        if not parsed_goal_spec.original_goal:
            parsed_goal_spec.original_goal = goal
            logger.debug("Set original_goal from input")
        
        # Ensure we have at least some entities or intent
        if not parsed_goal_spec.entities and not parsed_goal_spec.intent:
            logger.error(
                "Failed to extract meaningful entities or intent",
                extra={
                    "entities_count": len(parsed_goal_spec.entities) if parsed_goal_spec.entities else 0,
                    "intent_present": bool(parsed_goal_spec.intent)
                }
            )
            raise ValidationError("Could not extract meaningful entities or intent from goal")
        
        logger.debug("Goal validation passed")
        
        # Convert to dictionary for state storage
        parsed_goal_dict = parsed_goal_spec.model_dump()
        logger.debug("Converted parsed goal to dictionary", extra={"dict_keys": list(parsed_goal_dict.keys())})
        
        # Determine next step based on complexity and parsing results
        next_step = _determine_next_step(parsed_goal_spec, current_attempt)
        logger.info(
            "Determined next step",
            extra={
                "next_step": next_step,
                "complexity": parsed_goal_spec.complexity.value if parsed_goal_spec.complexity else None,
                "is_simple": parsed_goal_spec.is_simple_goal()
            }
        )
        
        result = ParseGoalResponse(
            current_step=next_step,
            current_attempt=1,  # Reset attempt counter for next phase
            artifacts=[Artifact(type="parsed_goal", data=parsed_goal_dict)],
            progress=[f"Parsed goal: {parsed_goal_spec.intent}"],
            result=ParseGoalResult(
                status="success",
                parsed_goal=parsed_goal_dict,
                complexity=parsed_goal_spec.complexity.value if parsed_goal_spec.complexity else None,
                requires_graph_ops=parsed_goal_spec.requires_graph_operations(),
                is_simple=parsed_goal_spec.is_simple_goal()
            )
        )
        
        logger.info(
            "Goal parsing completed successfully",
            extra={
                "next_step": next_step,
                "complexity": parsed_goal_spec.complexity.value if parsed_goal_spec.complexity else None,
                "requires_graph_ops": parsed_goal_spec.requires_graph_operations(),
                "is_simple": parsed_goal_spec.is_simple_goal()
            }
        )
        
        return result
        
    except ValidationError as e:
        # Handle validation errors (these are usually not retryable)
        error_msg = f"Goal validation failed: {str(e)}"
        
        logger.exception(
            "Goal validation failed",
            extra={
                "error": str(e),
                "error_type": "ValidationError",
                "current_attempt": current_attempt,
                "goal_length": len(goal)
            }
        )
        
        return ParseGoalResponse(
            current_step="escalate",
            current_attempt=current_attempt,
            failures=[Failure(step="parse_goal", error=error_msg, attempt=current_attempt, error_type="validation_error")],
            result=ParseGoalResult(
                status="error",
                error=error_msg,
                error_type="validation_error",
                retryable=False
            )
        )
        
    except Exception as e:
        # Handle other parsing errors gracefully
        error_msg = f"Goal parsing failed: {str(e)}"
        error_type = type(e).__name__
        
        # Classify error type for better handling
        if "timeout" in str(e).lower() or "connection" in str(e).lower():
            error_classification = "network_error"
        elif "api" in str(e).lower() or "key" in str(e).lower():
            error_classification = "api_error"
        elif "validation" in str(e).lower() or "schema" in str(e).lower():
            error_classification = "schema_error"
        else:
            error_classification = "unknown_error"
        
        logger.exception(
            "Goal parsing failed with exception",
            extra={
                "error": str(e),
                "error_type": error_type,
                "error_classification": error_classification,
                "current_attempt": current_attempt,
                "goal_length": len(goal)
            }
        )
        
        # If this is attempt 1, we might try with more context later
        if current_attempt == 1 and error_classification in ["network_error", "unknown_error"]:
            logger.info("First attempt failed, will retry with diagnosis", extra={"attempt": current_attempt, "error_classification": error_classification})
            return ParseGoalResponse(
                current_step="diagnose",
                current_attempt=current_attempt + 1,
                failures=[Failure(step="parse_goal", error=error_msg, attempt=current_attempt, error_type=error_classification)],
                result=ParseGoalResult(
                    status="error",
                    error=error_msg,
                    error_type=error_classification,
                    retryable=True
                )
            )
        else:
            # Multiple attempts failed or non-retryable error, escalate
            logger.error("Multiple attempts failed or non-retryable error, escalating to human", 
                        extra={"attempt": current_attempt, "error_classification": error_classification})
            return ParseGoalResponse(
                current_step="escalate",
                current_attempt=current_attempt,
                failures=[Failure(step="parse_goal", error=error_msg, attempt=current_attempt, error_type=error_classification)],
                result=ParseGoalResult(
                    status="error",
                    error=error_msg,
                    error_type=error_classification,
                    retryable=error_classification in ["network_error", "unknown_error"]
                )
            )


def _determine_next_step(goal_spec: GoalSpec, current_attempt: int) -> str:
    """Determine the next step based on parsed goal characteristics.
    
    Args:
        goal_spec: The parsed goal specification.
        current_attempt: Current attempt number.
        
    Returns:
        The next step to execute.
    """
    logger = get_logger(__name__)
    
    # Simple goals might skip planning
    if goal_spec.is_simple_goal() and goal_spec.complexity == GoalComplexity.SIMPLE:
        logger.debug("Simple goal detected, routing to tool", extra={"complexity": goal_spec.complexity.value})
        return "route_tool"
    
    # Complex goals need planning
    if goal_spec.complexity in [GoalComplexity.MEDIUM, GoalComplexity.COMPLEX]:
        logger.debug("Complex goal detected, routing to planning", extra={"complexity": goal_spec.complexity.value})
        return "plan_step"
    
    # Default to planning for safety
    logger.debug("Defaulting to planning step for safety", extra={"complexity": goal_spec.complexity.value if goal_spec.complexity else None})
    return "plan_step"
