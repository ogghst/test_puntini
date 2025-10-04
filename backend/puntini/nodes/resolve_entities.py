"""Resolve entities node implementation (Phase 2 of two-phase parsing).

This module implements the second phase of the two-phase parsing architecture
as specified in Phase 2 of the progressive refactoring plan. It resolves
entities with graph context, addressing the critical problem of no graph-aware
entity recognition identified in the graph critics analysis.
"""

from typing import Any, Dict, List, Optional, TYPE_CHECKING
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime, get_runtime
from langchain_core.language_models.chat_models import BaseChatModel

if TYPE_CHECKING:
    from ..orchestration.state_schema import State
from ..models.intent_schemas import IntentSpec, ResolvedGoalSpec, ResolvedEntity, Ambiguity
from ..models.goal_schemas import GoalComplexity
from ..models.errors import ValidationError
from ..logging import get_logger
from .message import ParseGoalResponse, ParseGoalResult, Artifact, Failure, ErrorContext


def resolve_entities(state: "State", config: Optional[RunnableConfig] = None, runtime: Optional[Runtime] = None) -> ParseGoalResponse:
    """Resolve entities with graph context (Phase 2 of two-phase parsing).
    
    This node takes the parsed intent from Phase 1 and resolves entities
    against the graph context. This addresses the critical problem of
    no graph-aware entity recognition identified in the graph critics analysis.
    
    Args:
        state: Current agent state containing the parsed intent.
        config: Optional RunnableConfig for additional configuration.
        runtime: Optional Runtime context for additional runtime information.
        
    Returns:
        Updated state with resolved entities and goal specification.
        
    Raises:
        ValidationError: If entity resolution fails.
        
    Notes:
        This is Phase 2 of the two-phase parsing architecture:
        1. Parse minimal intent without graph context (Phase 1)
        2. Resolve entities with graph context (Phase 2)
        3. Handle ambiguities with user interaction if needed
        
        This implements the standard knowledge graph pipeline:
        Raw Text → Entity Mentions → Entity Candidates → Entity Linking → Resolved Entities
    """
    # Initialize logger for this module
    logger = get_logger(__name__)
    
    # Access state attributes - handle both dict and object access
    logger.debug(f"State type: {type(state)}, State value: {state}")
    
    if isinstance(state, dict):
        goal = state.get("goal")
        current_attempt = state.get("current_attempt", 1)
        parse_goal_response = state.get("parse_intent_response")
    else:
        goal = getattr(state, "goal", None)
        current_attempt = getattr(state, "current_attempt", 1)
        parse_goal_response = getattr(state, "parse_intent_response", None)
    
    # Validate required fields
    if not isinstance(goal, str):
        raise ValidationError("Goal must be a string")
    
    if not isinstance(current_attempt, int) or current_attempt < 1:
        raise ValidationError("Current attempt must be a positive integer")
    
    # Get the parsed intent from Phase 1
    if not parse_goal_response:
        raise ValidationError("No parsed intent found from Phase 1")
    
    # Extract intent spec from the response
    if isinstance(parse_goal_response, dict):
        parsed_goal_dict = parse_goal_response.get("result", {}).get("parsed_goal", {})
    else:
        parsed_goal_dict = parse_goal_response.result.parsed_goal if parse_goal_response.result else {}
    
    if not parsed_goal_dict:
        raise ValidationError("No parsed intent data found in response")
    
    try:
        # Reconstruct IntentSpec from the parsed data
        intent_spec = IntentSpec(**parsed_goal_dict)
    except Exception as e:
        raise ValidationError(f"Failed to reconstruct intent spec: {str(e)}")
    
    # Log function entry with context
    logger.info(
        "Starting entity resolution (Phase 2)",
        extra={
            "goal_length": len(goal),
            "current_attempt": current_attempt,
            "intent_type": intent_spec.intent_type.value,
            "mentioned_entities_count": len(intent_spec.mentioned_entities)
        }
    )
    
    try:
        # Get LLM from graph context
        logger.debug("Getting LLM from graph context for entity resolution")
        
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
        
        llm: BaseChatModel = runtime.context['llm']
        
        # Get graph store from context for entity resolution
        graph_store = None
        if hasattr(runtime, 'context') and 'graph_store' in runtime.context:
            graph_store = runtime.context['graph_store']
            logger.debug("Found graph store in runtime context")
        else:
            logger.warning("No graph store found in runtime context, using mock resolution")
      
        # Create structured LLM for entity resolution
        structured_llm = llm.with_structured_output(ResolvedGoalSpec)
        
        logger.info(
            "Using LLM from graph context for entity resolution",
            extra={
                "llm_type": type(llm).__name__,
                "target_model": ResolvedGoalSpec.__name__,
                "has_graph_store": graph_store is not None
            }
        )
        
        # Create prompt for entity resolution (with graph context)
        logger.debug("Creating entity resolution prompt template")
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Resolve entities from intent with graph context.

You have an intent specification with mentioned entities. Resolve these entities
against the graph context to create a complete goal specification.

Input Intent:
- intent_type: {intent_type}
- mentioned_entities: {mentioned_entities}
- requires_graph_context: {requires_graph_context}
- complexity: {complexity}

For each mentioned entity:
1. Check if it exists in the graph context
2. If it exists, provide entity_id, name, type, and confidence score
3. If it doesn't exist, mark as new entity to be created
4. If ambiguous (multiple matches), create ambiguity for user disambiguation

Graph Context (if available):
{graph_context}

Output Requirements:
- entities: List of resolved entities with graph context
- ambiguities: List of ambiguous references requiring user input
- ready_to_execute: Whether the goal is ready for execution

Entity Resolution Rules:
- Use entity_id from graph if entity exists
- Set confidence based on name similarity and context
- Mark as is_new=true if entity doesn't exist
- Create ambiguity if confidence < 0.7 and multiple candidates
- Set ready_to_execute=false if there are ambiguities

Be precise with confidence scores and conservative with ambiguity detection."""),
            ("human", "Resolve entities for this intent: {goal}")
        ])
        
        # Get graph context for the prompt
        graph_context = _get_graph_context(graph_store, intent_spec.mentioned_entities)
        
        # Create the parsing chain
        logger.debug("Creating entity resolution chain")
        parsing_chain = prompt | structured_llm
        
        # Resolve entities
        logger.info("Invoking LLM for entity resolution", extra={"goal_preview": goal[:100] + "..." if len(goal) > 100 else goal})
        
        try:
            resolved_goal: ResolvedGoalSpec = parsing_chain.invoke({
                "goal": goal,
                "intent_type": intent_spec.intent_type.value,
                "mentioned_entities": intent_spec.mentioned_entities,
                "requires_graph_context": intent_spec.requires_graph_context,
                "complexity": intent_spec.complexity.value,
                "graph_context": graph_context
            })
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
                raise ValidationError(f"Entity resolution failed: LLM response was truncated or malformed. This usually indicates the response exceeded token limits. Error: {str(e)}")
            else:
                # Re-raise other exceptions to be handled by outer try-catch
                raise
        
        logger.info(
            "Successfully resolved entities",
            extra={
                "resolved_entities_count": len(resolved_goal.entities),
                "ambiguities_count": len(resolved_goal.ambiguities),
                "ready_to_execute": resolved_goal.ready_to_execute
            }
        )
        
        # Validate the resolved goal
        logger.debug("Validating resolved goal specification")
        
        # Ensure we have at least some resolved entities
        if not resolved_goal.entities and intent_spec.mentioned_entities:
            logger.error(
                "Failed to resolve any entities",
                extra={
                    "mentioned_entities": intent_spec.mentioned_entities,
                    "resolved_entities_count": len(resolved_goal.entities)
                }
            )
            raise ValidationError("Could not resolve any entities from the mentioned entities")
        
        logger.debug("Entity resolution validation passed")
        
        # Convert to dictionary for state storage
        resolved_goal_dict = resolved_goal.model_dump()
        logger.debug("Converted resolved goal to dictionary", extra={"dict_keys": list(resolved_goal_dict.keys())})
        
        # Determine next step based on resolution results
        next_step = _determine_next_step(resolved_goal, current_attempt)
        logger.info(
            "Determined next step",
            extra={
                "next_step": next_step,
                "has_ambiguities": resolved_goal.has_ambiguities(),
                "ready_to_execute": resolved_goal.ready_to_execute
            }
        )
        
        result = ParseGoalResponse(
            current_step=next_step,
            current_attempt=1,  # Reset attempt counter for next phase
            artifacts=[],  # No artifacts needed for entity resolution
            progress=[f"Resolved {len(resolved_goal.entities)} entities"],
            result=ParseGoalResult(
                status="success",
                parsed_goal=resolved_goal_dict,
                complexity=intent_spec.complexity.value,
                requires_graph_ops=True,  # Entity resolution always requires graph ops
                is_simple=resolved_goal.ready_to_execute and not resolved_goal.has_ambiguities()
            ),
            goal_spec=None,  # Store resolved goal spec separately
            todo_list=[]  # No todo list yet - that comes in planning
        )
        
        logger.info(
            "Entity resolution completed successfully",
            extra={
                "next_step": next_step,
                "resolved_entities_count": len(resolved_goal.entities),
                "ambiguities_count": len(resolved_goal.ambiguities),
                "ready_to_execute": resolved_goal.ready_to_execute
            }
        )
        
        return result
        
    except ValidationError as e:
        # Handle validation errors (these are usually not retryable)
        error_msg = f"Entity resolution validation failed: {str(e)}"
        
        logger.exception(
            "Entity resolution validation failed",
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
            failures=[Failure(step="resolve_entities", error=error_msg, attempt=current_attempt, error_type="validation_error")],
            result=ParseGoalResult(
                status="error",
                error=error_msg,
                error_type="validation_error",
                retryable=False
            )
        )
        
    except Exception as e:
        # Handle other resolution errors gracefully
        error_msg = f"Entity resolution failed: {str(e)}"
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
            "Entity resolution failed with exception",
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
                failures=[Failure(step="resolve_entities", error=error_msg, attempt=current_attempt, error_type=error_classification)],
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
                failures=[Failure(step="resolve_entities", error=error_msg, attempt=current_attempt, error_type=error_classification)],
                result=ParseGoalResult(
                    status="error",
                    error=error_msg,
                    error_type=error_classification,
                    retryable=error_classification in ["network_error", "unknown_error"]
                )
            )


def _get_graph_context(graph_store, mentioned_entities: List[str]) -> str:
    """Get relevant graph context for entity resolution.
    
    Args:
        graph_store: The graph store instance.
        mentioned_entities: List of mentioned entity names.
        
    Returns:
        String representation of relevant graph context.
    """
    if not graph_store or not mentioned_entities:
        return "No graph context available"
    
    try:
        # This is a simplified implementation
        # In a real implementation, you would query the graph store
        # for entities similar to the mentioned ones
        context_parts = []
        for entity in mentioned_entities:
            # Mock graph query - in reality, this would use the graph store
            context_parts.append(f"Entity '{entity}': No existing matches found")
        
        return "\n".join(context_parts)
    except Exception:
        return "Error retrieving graph context"


def _determine_next_step(resolved_goal: ResolvedGoalSpec, current_attempt: int) -> str:
    """Determine the next step based on entity resolution results.
    
    Args:
        resolved_goal: The resolved goal specification.
        current_attempt: Current attempt number.
        
    Returns:
        The next step to execute.
    """
    logger = get_logger(__name__)
    
    # If there are ambiguities, go to disambiguation
    if resolved_goal.has_ambiguities():
        logger.debug("Found ambiguities, routing to disambiguation", 
                    extra={"ambiguities_count": len(resolved_goal.ambiguities)})
        return "disambiguate"
    
    # If ready to execute, go to planning
    if resolved_goal.ready_to_execute:
        logger.debug("Goal ready to execute, routing to planning", 
                    extra={"resolved_entities_count": len(resolved_goal.entities)})
        return "plan_step"
    
    # Default to planning for further processing
    logger.debug("Routing to planning for further processing", 
                extra={"resolved_entities_count": len(resolved_goal.entities)})
    return "plan_step"
