"""Parse intent node implementation (Phase 1 of two-phase parsing).

This module implements the first phase of the two-phase parsing architecture
as specified in Phase 2 of the progressive refactoring plan. It extracts
minimal intent without graph context, addressing the critical problem of
premature full goal parsing identified in the graph critics analysis.
"""

from typing import Any, Dict, Optional, TYPE_CHECKING
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime, get_runtime
from langchain_core.language_models.chat_models import BaseChatModel

if TYPE_CHECKING:
    from ..orchestration.state_schema import State
from ..models.intent_schemas import IntentSpec, IntentType
from ..models.goal_schemas import GoalComplexity
from ..models.errors import ValidationError
from ..logging import get_logger
from .message import ParseGoalResponse, ParseGoalResult, Artifact, Failure, ErrorContext


def parse_intent(state: "State", config: Optional[RunnableConfig] = None, runtime: Optional[Runtime] = None) -> ParseGoalResponse:
    """Parse minimal intent without graph context (Phase 1 of two-phase parsing).
    
    This node extracts only the essential intent information without attempting
    to resolve entities against the graph. This addresses the critical problem
    of premature entity extraction without graph context identified in the
    graph critics analysis.
    
    Args:
        state: Current agent state containing the goal.
        config: Optional RunnableConfig for additional configuration.
        runtime: Optional Runtime context for additional runtime information.
        
    Returns:
        Updated state with parsed intent information.
        
    Raises:
        ValidationError: If the intent cannot be parsed or validated.
        
    Notes:
        This is Phase 1 of the two-phase parsing architecture:
        1. Parse minimal intent without graph context
        2. Route based on complexity and graph context requirements
        3. Later: resolve entities with graph context in resolve_entities node
        
        This addresses the progressive context disclosure principle by
        only extracting what's immediately parsable without overwhelming context.
    """
    # Initialize logger for this module
    logger = get_logger(__name__)
    
    # Access state attributes - handle both dict and object access
    logger.debug(f"State type: {type(state)}, State value: {state}")
    
    if isinstance(state, dict):
        goal = state.get("goal")
        current_attempt = state.get("current_attempt", 1)
    else:
        goal = getattr(state, "goal", None)
        current_attempt = getattr(state, "current_attempt", 1)
    
    # Validate required fields
    if not isinstance(goal, str):
        raise ValidationError("Goal must be a string")
    
    if not isinstance(current_attempt, int) or current_attempt < 1:
        raise ValidationError("Current attempt must be a positive integer")
    
    # Log function entry with context
    logger.info(
        "Starting intent parsing (Phase 1)",
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
        logger.debug("Getting LLM from graph context for intent parsing")
        
        # Get the runtime context to access the configured LLM
        if runtime is None:
            # Fallback to get_runtime if runtime is not passed directly
            try:
                runtime = get_runtime()
            except Exception as e:
                logger.error(f"Failed to get runtime context: {e}")
                raise ValidationError("Runtime context not available for LLM access")
        
        # Get the LLM from the context
        if not hasattr(runtime, 'context') or runtime.context is None or 'llm' not in runtime.context:
            logger.error("LLM not found in runtime context")
            raise ValidationError("LLM not configured in graph context")
        
        llm: BaseChatModel = runtime.context['llm']
      
        # Create structured LLM for intent parsing
        structured_llm = llm.with_structured_output(IntentSpec)
        
        logger.info(
            "Using LLM from graph context for intent parsing",
            extra={
                "llm_type": type(llm).__name__,
                "target_model": IntentSpec.__name__
            }
        )
        
        # Create prompt for intent parsing (progressive disclosure - minimal context)
        logger.debug("Creating intent parsing prompt template")
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Parse natural language goals to extract minimal intent without graph context.

Extract ONLY:
1. INTENT_TYPE: create, query, update, delete, or unknown
2. MENTIONED_ENTITIES: Just the entity names as strings (e.g., ["John", "Project Alpha"])
3. REQUIRES_GRAPH_CONTEXT: Whether you need to look at existing graph data
4. COMPLEXITY: simple, medium, or complex
5. ORIGINAL_GOAL: The input text

IMPORTANT:
- Do NOT attempt to resolve entities against any graph
- Do NOT extract properties or detailed entity information
- Do NOT create entity specifications
- Just identify what entities are mentioned as strings
- Focus on intent and complexity for routing decisions

Examples:
- "Create a user John" → intent_type: create, mentioned_entities: ["John"], requires_graph_context: true
- "Show me all projects" → intent_type: query, mentioned_entities: ["projects"], requires_graph_context: true
- "What's the weather?" → intent_type: query, mentioned_entities: [], requires_graph_context: false

Be conservative with complexity and keep responses minimal."""),
            ("human", "Parse this goal for minimal intent: {goal}")
        ])
        
        # Create the parsing chain
        logger.debug("Creating intent parsing chain")
        parsing_chain = prompt | structured_llm
        
        # Parse the intent
        logger.info("Invoking LLM for intent parsing", extra={"goal_preview": goal[:100] + "..." if len(goal) > 100 else goal})
        
        try:
            parsed_intent: IntentSpec = parsing_chain.invoke({"goal": goal})
        except Exception as e:
            # Check if this is a JSON parsing error (likely due to truncation)
            if "JSONDecodeError" in str(e) or "Expecting value" in str(e) or "OUTPUT_PARSING_FAILURE" in str(e):
                logger.error(
                    "JSON parsing failed - likely due to response truncation",
                    extra={
                        "error": str(e),
                        "error_type": "json_parsing_error",
                        "current_attempt": current_attempt,
                        "goal_length": len(goal),
                        "llm_max_tokens": getattr(llm, 'max_tokens', 'unknown')
                    }
                )
                raise ValidationError(f"Intent parsing failed: LLM response was truncated or malformed. This usually indicates the response exceeded token limits. Error: {str(e)}")
            else:
                # Re-raise other exceptions to be handled by outer try-catch
                raise
        
        logger.info(
            "Successfully parsed intent",
            extra={
                "intent_type": parsed_intent.intent_type.value,
                "mentioned_entities_count": len(parsed_intent.mentioned_entities),
                "requires_graph_context": parsed_intent.requires_graph_context,
                "complexity": parsed_intent.complexity.value
            }
        )
        
        # Validate the parsed intent
        logger.debug("Validating parsed intent specification")
        if not parsed_intent.original_goal:
            parsed_intent.original_goal = goal
            logger.debug("Set original_goal from input")
        
        # Ensure we have at least some intent information
        if not parsed_intent.intent_type or parsed_intent.intent_type == IntentType.UNKNOWN:
            logger.error(
                "Failed to extract meaningful intent",
                extra={
                    "intent_type": parsed_intent.intent_type.value if parsed_intent.intent_type else None,
                    "mentioned_entities_count": len(parsed_intent.mentioned_entities)
                }
            )
            raise ValidationError("Could not extract meaningful intent from goal")
        
        logger.debug("Intent validation passed")
        
        # Convert to dictionary for state storage
        parsed_intent_dict = parsed_intent.model_dump()
        logger.debug("Converted parsed intent to dictionary", extra={"dict_keys": list(parsed_intent_dict.keys())})
        
        # Determine next step based on intent characteristics
        next_step = _determine_next_step(parsed_intent, current_attempt)
        logger.info(
            "Determined next step",
            extra={
                "next_step": next_step,
                "intent_type": parsed_intent.intent_type.value,
                "requires_graph_context": parsed_intent.requires_graph_context,
                "is_simple": parsed_intent.is_simple_intent()
            }
        )
        
        result = ParseGoalResponse(
            current_step=next_step,
            current_attempt=1,  # Reset attempt counter for next phase
            artifacts=[],  # No artifacts needed for intent parsing
            progress=[f"Parsed intent: {parsed_intent.intent_type.value}"],
            result=ParseGoalResult(
                status="success",
                parsed_goal=parsed_intent_dict,
                complexity=parsed_intent.complexity.value,
                requires_graph_ops=parsed_intent.requires_graph_context,
                is_simple=parsed_intent.is_simple_intent()
            ),
            goal_spec=None,  # No full goal spec yet - that comes in Phase 2
            todo_list=[]  # No todo list yet - that comes in Phase 2
        )
        
        logger.info(
            "Intent parsing completed successfully",
            extra={
                "next_step": next_step,
                "intent_type": parsed_intent.intent_type.value,
                "requires_graph_context": parsed_intent.requires_graph_context,
                "is_simple": parsed_intent.is_simple_intent()
            }
        )
        
        return result
        
    except ValidationError as e:
        # Handle validation errors (these are usually not retryable)
        error_msg = f"Intent validation failed: {str(e)}"
        
        logger.exception(
            "Intent validation failed",
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
            failures=[Failure(step="parse_intent", error=error_msg, attempt=current_attempt, error_type="validation_error")],
            result=ParseGoalResult(
                status="error",
                error=error_msg,
                error_type="validation_error",
                retryable=False
            )
        )
        
    except Exception as e:
        # Handle other parsing errors gracefully
        error_msg = f"Intent parsing failed: {str(e)}"
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
            "Intent parsing failed with exception",
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
                failures=[Failure(step="parse_intent", error=error_msg, attempt=current_attempt, error_type=error_classification)],
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
                failures=[Failure(step="parse_intent", error=error_msg, attempt=current_attempt, error_type=error_classification)],
                result=ParseGoalResult(
                    status="error",
                    error=error_msg,
                    error_type=error_classification,
                    retryable=error_classification in ["network_error", "unknown_error"]
                )
            )


def _determine_next_step(intent_spec: IntentSpec, current_attempt: int) -> str:
    """Determine the next step based on parsed intent characteristics.
    
    Args:
        intent_spec: The parsed intent specification.
        current_attempt: Current attempt number.
        
    Returns:
        The next step to execute.
    """
    logger = get_logger(__name__)
    
    # If the intent requires graph context, go to entity resolution
    if intent_spec.requires_graph_context:
        logger.debug("Intent requires graph context, routing to entity resolution", 
                    extra={"intent_type": intent_spec.intent_type.value})
        return "resolve_entities"
    
    # If it's a simple intent that doesn't need graph context, go to planning
    if intent_spec.is_simple_intent():
        logger.debug("Simple intent, routing to planning", 
                    extra={"intent_type": intent_spec.intent_type.value})
        return "plan_step"
    
    # For complex intents without graph context, still go to planning
    # The planning step will determine if graph context is needed
    logger.debug("Complex intent, routing to planning", 
                extra={"intent_type": intent_spec.intent_type.value, "complexity": intent_spec.complexity.value})
    return "plan_step"
