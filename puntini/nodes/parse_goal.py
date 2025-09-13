"""Parse goal node implementation.

This module implements the parse_goal node that extracts goal,
constraints, and domain hints as structured data using LangChain
and Pydantic models for robust parsing and validation.
"""

from typing import Any, Dict, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime

from ..orchestration.state import State
from ..models.goal_schemas import GoalSpec, GoalComplexity
from ..models.errors import ValidationError
from ..logging import get_logger
from ..llm.llm_models import LLMFactory


def parse_goal(state: State, config: Optional[RunnableConfig] = None, runtime: Optional[Runtime] = None) -> Dict[str, Any]:
    """Parse the goal and extract structured information using LLM.
    
    This node extracts the goal, constraints, and domain hints from
    the input using LangChain's structured output capabilities and
    Pydantic models for validation.
    
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
    """
    # Initialize logger for this module
    logger = get_logger(__name__)
    
    # Validate state input
    if not isinstance(state, dict):
        raise ValidationError("State must be a dictionary")
    
    goal = state.get("goal", "")
    current_attempt = state.get("current_attempt", 1)
    
    # Validate required fields
    if not isinstance(goal, str):
        raise ValidationError("Goal must be a string")
    
    if not isinstance(current_attempt, int) or current_attempt < 1:
        raise ValidationError("Current attempt must be a positive integer")
    
    # Log function entry with context
    logger.info(
        "Starting goal parsing",
        goal_length=len(goal),
        current_attempt=current_attempt,
        state_keys=list(state.keys())
    )
    
    if not goal.strip():
        logger.error("Empty goal provided", goal=goal)
        raise ValidationError("Goal cannot be empty")
    
    try:
        # Get LLM from factory
        logger.debug("Initializing LLM factory for goal parsing")
        llm_factory = LLMFactory()
        # Use default LLM instead of hardcoded "ollama"
        structured_llm = llm_factory.create_structured_llm(None, GoalSpec)
        
        logger.info(
            "Created structured LLM for goal parsing",
            llm_type="default",
            target_model=GoalSpec.__name__
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
        logger.info("Invoking LLM for goal parsing", goal_preview=goal[:100] + "..." if len(goal) > 100 else goal)
        parsed_goal_spec = parsing_chain.invoke({"goal": goal})
        
        logger.info(
            "Successfully parsed goal",
            parsed_entities=len(parsed_goal_spec.entities) if parsed_goal_spec.entities else 0,
            complexity=parsed_goal_spec.complexity.value if parsed_goal_spec.complexity else None,
            intent_length=len(parsed_goal_spec.intent) if parsed_goal_spec.intent else 0
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
                entities_count=len(parsed_goal_spec.entities) if parsed_goal_spec.entities else 0,
                intent_present=bool(parsed_goal_spec.intent)
            )
            raise ValidationError("Could not extract meaningful entities or intent from goal")
        
        logger.debug("Goal validation passed")
        
        # Convert to dictionary for state storage
        parsed_goal_dict = parsed_goal_spec.model_dump()
        logger.debug("Converted parsed goal to dictionary", dict_keys=list(parsed_goal_dict.keys()))
        
        # Determine next step based on complexity and parsing results
        next_step = _determine_next_step(parsed_goal_spec, current_attempt)
        logger.info(
            "Determined next step",
            next_step=next_step,
            complexity=parsed_goal_spec.complexity.value if parsed_goal_spec.complexity else None,
            is_simple=parsed_goal_spec.is_simple_goal()
        )
        
        result = {
            "current_step": next_step,
            "current_attempt": 1,  # Reset attempt counter for next phase
            "artifacts": [{"type": "parsed_goal", "data": parsed_goal_dict}],
            "progress": [f"Parsed goal: {parsed_goal_spec.intent}"],
            "result": {
                "status": "success",
                "parsed_goal": parsed_goal_dict,
                "complexity": parsed_goal_spec.complexity,
                "requires_graph_ops": parsed_goal_spec.requires_graph_operations(),
                "is_simple": parsed_goal_spec.is_simple_goal()
            }
        }
        
        logger.info(
            "Goal parsing completed successfully",
            next_step=next_step,
            complexity=parsed_goal_spec.complexity.value if parsed_goal_spec.complexity else None,
            requires_graph_ops=parsed_goal_spec.requires_graph_operations(),
            is_simple=parsed_goal_spec.is_simple_goal()
        )
        
        return result
        
    except ValidationError as e:
        # Handle validation errors (these are usually not retryable)
        error_msg = f"Goal validation failed: {str(e)}"
        
        logger.error(
            "Goal validation failed",
            error=str(e),
            error_type="ValidationError",
            current_attempt=current_attempt,
            goal_length=len(goal)
        )
        
        return {
            "current_step": "escalate",
            "current_attempt": current_attempt,
            "failures": [{"step": "parse_goal", "error": error_msg, "attempt": current_attempt, "error_type": "validation_error"}],
            "result": {
                "status": "error",
                "error": error_msg,
                "error_type": "validation_error",
                "retryable": False
            }
        }
        
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
        
        logger.error(
            "Goal parsing failed with exception",
            error=str(e),
            error_type=error_type,
            error_classification=error_classification,
            current_attempt=current_attempt,
            goal_length=len(goal)
        )
        
        # If this is attempt 1, we might try with more context later
        if current_attempt == 1 and error_classification in ["network_error", "unknown_error"]:
            logger.info("First attempt failed, will retry with diagnosis", attempt=current_attempt, error_classification=error_classification)
            return {
                "current_step": "diagnose",
                "current_attempt": current_attempt + 1,
                "failures": [{"step": "parse_goal", "error": error_msg, "attempt": current_attempt, "error_type": error_classification}],
                "result": {
                    "status": "error",
                    "error": error_msg,
                    "error_type": error_classification,
                    "retryable": True
                }
            }
        else:
            # Multiple attempts failed or non-retryable error, escalate
            logger.error("Multiple attempts failed or non-retryable error, escalating to human", 
                        attempt=current_attempt, error_classification=error_classification)
            return {
                "current_step": "escalate",
                "current_attempt": current_attempt,
                "failures": [{"step": "parse_goal", "error": error_msg, "attempt": current_attempt, "error_type": error_classification}],
                "result": {
                    "status": "error",
                    "error": error_msg,
                    "error_type": error_classification,
                    "retryable": error_classification in ["network_error", "unknown_error"]
                }
            }


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
        logger.debug("Simple goal detected, routing to tool", complexity=goal_spec.complexity.value)
        return "route_tool"
    
    # Complex goals need planning
    if goal_spec.complexity in [GoalComplexity.MEDIUM, GoalComplexity.COMPLEX]:
        logger.debug("Complex goal detected, routing to planning", complexity=goal_spec.complexity.value)
        return "plan_step"
    
    # Default to planning for safety
    logger.debug("Defaulting to planning step for safety", complexity=goal_spec.complexity.value if goal_spec.complexity else None)
    return "plan_step"
