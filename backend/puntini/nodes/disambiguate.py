"""Disambiguation node implementation for handling ambiguous entity references.

This module implements the disambiguation node that handles ambiguous entity
references with user interaction, as specified in Phase 2 of the progressive
refactoring plan. This addresses the critical problem of no handling of
ambiguous references identified in the graph critics analysis.
"""

from typing import Any, Dict, List, Optional, TYPE_CHECKING
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime, get_runtime
from langchain_core.language_models.chat_models import BaseChatModel
from langgraph.types import interrupt

if TYPE_CHECKING:
    from ..orchestration.state_schema import State
from ..models.intent_schemas import ResolvedGoalSpec, Ambiguity, ResolvedEntity
from ..models.errors import ValidationError
from ..logging import get_logger
from .message import ParseGoalResponse, ParseGoalResult, Artifact, Failure, ErrorContext


def disambiguate(state: "State", config: Optional[RunnableConfig] = None, runtime: Optional[Runtime] = None) -> ParseGoalResponse:
    """Handle ambiguous entity references with user interaction.
    
    This node presents ambiguous entity references to the user and waits
    for their input to resolve the ambiguities. This addresses the critical
    problem of no handling of ambiguous references identified in the
    graph critics analysis.
    
    Args:
        state: Current agent state containing resolved entities with ambiguities.
        config: Optional RunnableConfig for additional configuration.
        runtime: Optional Runtime context for additional runtime information.
        
    Returns:
        Updated state with disambiguation results.
        
    Raises:
        ValidationError: If disambiguation fails.
        
    Notes:
        This node implements human-in-the-loop functionality by interrupting
        execution to wait for human input. The agent will pause and wait
        for human intervention before resuming execution.
        
        This addresses the progressive context disclosure principle by
        asking for user input only when necessary for disambiguation.
    """
    # Initialize logger for this module
    logger = get_logger(__name__)
    
    # Access state attributes - handle both dict and object access
    logger.debug(f"State type: {type(state)}, State value: {state}")
    
    if isinstance(state, dict):
        goal = state.get("goal")
        current_attempt = state.get("current_attempt", 1)
        parse_goal_response = state.get("parse_goal_response")
    else:
        goal = getattr(state, "goal", None)
        current_attempt = getattr(state, "current_attempt", 1)
        parse_goal_response = getattr(state, "parse_goal_response", None)
    
    # Validate required fields
    if not isinstance(goal, str):
        raise ValidationError("Goal must be a string")
    
    if not isinstance(current_attempt, int) or current_attempt < 1:
        raise ValidationError("Current attempt must be a positive integer")
    
    # Get the resolved goal from Phase 2
    if not parse_goal_response:
        raise ValidationError("No resolved goal found from Phase 2")
    
    # Extract resolved goal from the response
    if isinstance(parse_goal_response, dict):
        resolved_goal_dict = parse_goal_response.get("result", {}).get("parsed_goal", {})
    else:
        resolved_goal_dict = parse_goal_response.result.parsed_goal if parse_goal_response.result else {}
    
    if not resolved_goal_dict:
        raise ValidationError("No resolved goal data found in response")
    
    try:
        # Reconstruct ResolvedGoalSpec from the parsed data
        resolved_goal: ResolvedGoalSpec = ResolvedGoalSpec(**resolved_goal_dict)
    except Exception as e:
        raise ValidationError(f"Failed to reconstruct resolved goal spec: {str(e)}")
    
    # Log function entry with context
    logger.info(
        "Starting disambiguation",
        extra={
            "goal_length": len(goal),
            "current_attempt": current_attempt,
            "ambiguities_count": len(resolved_goal.ambiguities),
            "resolved_entities_count": len(resolved_goal.entities)
        }
    )
    
    # Check if there are actually ambiguities to resolve
    if not resolved_goal.has_ambiguities():
        logger.warning("No ambiguities found, routing to planning")
        return ParseGoalResponse(
            current_step="plan_step",
            current_attempt=1,
            artifacts=[],
            progress=["No ambiguities found, proceeding to planning"],
            result=ParseGoalResult(
                status="success",
                parsed_goal=resolved_goal_dict,
                complexity=resolved_goal.intent_spec.complexity.value,
                requires_graph_ops=True,
                is_simple=resolved_goal.ready_to_execute
            )
        )
    
    try:
        # Get LLM from graph context for generating disambiguation questions
        logger.debug("Getting LLM from graph context for disambiguation")
        
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
        
        # Create prompt for generating disambiguation questions
        logger.debug("Creating disambiguation prompt template")
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Generate clear disambiguation questions for ambiguous entity references.

You have a resolved goal with ambiguous entities that need user input to resolve.
Generate clear, concise questions that help the user choose the correct entity.

Input:
- Original goal: {goal}
- Ambiguities: {ambiguities}

For each ambiguity, generate:
1. A clear question asking the user to choose
2. A list of candidate options with descriptions
3. Context to help the user make the right choice

Format the response as a clear disambiguation message that can be presented to the user.
Keep it concise but informative."""),
            ("human", "Generate disambiguation questions for these ambiguities: {ambiguities}")
        ])
        
        # Create the disambiguation chain
        logger.debug("Creating disambiguation chain")
        disambiguation_chain = prompt | llm
        
        # Generate disambiguation questions
        logger.info("Invoking LLM for disambiguation questions", extra={"ambiguities_count": len(resolved_goal.ambiguities)})
        
        try:
            # Convert ambiguities to a readable format
            ambiguities_text = _format_ambiguities_for_prompt(resolved_goal.ambiguities)
            
            disambiguation_response = disambiguation_chain.invoke({
                "goal": goal,
                "ambiguities": ambiguities_text
            })
            
            # Extract the disambiguation message
            if hasattr(disambiguation_response, 'content'):
                disambiguation_message = disambiguation_response.content
            else:
                disambiguation_message = str(disambiguation_response)
                
        except Exception as e:
            logger.error(f"Failed to generate disambiguation questions: {e}")
            # Fallback to a simple disambiguation message
            disambiguation_message = _generate_fallback_disambiguation_message(resolved_goal.ambiguities)
        
        logger.info(
            "Generated disambiguation questions",
            extra={
                "disambiguation_message_length": len(disambiguation_message),
                "ambiguities_count": len(resolved_goal.ambiguities)
            }
        )
        
        # Create disambiguation context for human-in-the-loop
        disambiguation_context = {
            "type": "entity_disambiguation",
            "message": disambiguation_message,
            "ambiguities": [ambiguity.model_dump() for ambiguity in resolved_goal.ambiguities],
            "resolved_entities": [entity.model_dump() for entity in resolved_goal.entities],
            "original_goal": goal
        }
        
        # Interrupt for human input (human-in-the-loop)
        logger.info("Interrupting for human disambiguation input")
        interrupt(disambiguation_context)
        
        # Note: The execution will pause here and wait for human input
        # When resumed, the human input will be available in the state
        # This is handled by the LangGraph interrupt mechanism
        
        result = ParseGoalResponse(
            current_step="plan_step",  # Will be updated when resumed with human input
            current_attempt=1,
            artifacts=[],
            progress=["Waiting for user disambiguation input"],
            result=ParseGoalResult(
                status="success",
                parsed_goal=resolved_goal_dict,
                complexity=resolved_goal.intent_spec.complexity.value,
                requires_graph_ops=True,
                is_simple=False  # Disambiguation makes it not simple
            )
        )
        
        logger.info(
            "Disambiguation completed successfully",
            extra={
                "ambiguities_count": len(resolved_goal.ambiguities),
                "resolved_entities_count": len(resolved_goal.entities)
            }
        )
        
        return result
        
    except ValidationError as e:
        # Handle validation errors (these are usually not retryable)
        error_msg = f"Disambiguation validation failed: {str(e)}"
        
        logger.exception(
            "Disambiguation validation failed",
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
            failures=[Failure(step="disambiguate", error=error_msg, attempt=current_attempt, error_type="validation_error")],
            result=ParseGoalResult(
                status="error",
                error=error_msg,
                error_type="validation_error",
                retryable=False
            )
        )
        
    except Exception as e:
        # Handle other disambiguation errors gracefully
        error_msg = f"Disambiguation failed: {str(e)}"
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
            "Disambiguation failed with exception",
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
                failures=[Failure(step="disambiguate", error=error_msg, attempt=current_attempt, error_type=error_classification)],
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
                failures=[Failure(step="disambiguate", error=error_msg, attempt=current_attempt, error_type=error_classification)],
                result=ParseGoalResult(
                    status="error",
                    error=error_msg,
                    error_type=error_classification,
                    retryable=error_classification in ["network_error", "unknown_error"]
                )
            )


def _format_ambiguities_for_prompt(ambiguities: List[Ambiguity]) -> str:
    """Format ambiguities for the LLM prompt.
    
    Args:
        ambiguities: List of ambiguity objects.
        
    Returns:
        Formatted string representation of ambiguities.
    """
    if not ambiguities:
        return "No ambiguities"
    
    formatted_parts = []
    for i, ambiguity in enumerate(ambiguities, 1):
        formatted_parts.append(f"{i}. Mention: '{ambiguity.mention}'")
        formatted_parts.append(f"   Question: {ambiguity.disambiguation_question}")
        formatted_parts.append(f"   Context: {ambiguity.context}")
        formatted_parts.append(f"   Candidates: {len(ambiguity.candidates)} options")
        formatted_parts.append("")
    
    return "\n".join(formatted_parts)


def _generate_fallback_disambiguation_message(ambiguities: List[Ambiguity]) -> str:
    """Generate a fallback disambiguation message if LLM fails.
    
    Args:
        ambiguities: List of ambiguity objects.
        
    Returns:
        Fallback disambiguation message.
    """
    if not ambiguities:
        return "No ambiguities to resolve."
    
    message_parts = [
        "I need your help to resolve some ambiguous references:",
        ""
    ]
    
    for i, ambiguity in enumerate(ambiguities, 1):
        message_parts.append(f"{i}. For '{ambiguity.mention}': {ambiguity.disambiguation_question}")
        message_parts.append(f"   Context: {ambiguity.context}")
        message_parts.append("")
    
    message_parts.append("Please provide your choices to continue.")
    
    return "\n".join(message_parts)
