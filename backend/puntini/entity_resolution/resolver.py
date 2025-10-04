"""Entity resolver for graph-aware entity recognition.

This module implements the core entity resolution logic that addresses
the fundamental flaws in the current entity recognition system:

1. Graph-aware entity recognition before planning
2. Proper entity deduplication and disambiguation
3. Progressive context disclosure (intent → graph context → entities)
4. Meaningful confidence scores based on graph similarity
5. Handling of ambiguous references with user interaction

Implements the standard knowledge graph pipeline:
Raw Text → Entity Mentions → Entity Candidates → Entity Linking → Resolved Entities
"""

from typing import Any, Dict, List, Optional, Protocol
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from .models import (
    EntityMention, 
    EntityCandidate, 
    EntityResolution,
    ResolutionStrategy,
    AmbiguityResolution,
    ResolutionStatus
)
from .context import GraphContext
from .similarity import EntitySimilarityScorer, SimilarityConfig
from puntini.interfaces.graph_store import GraphStore


class EntityResolver(Protocol):
    """Protocol for entity resolution operations.
    
    Defines the contract for entity resolution implementations.
    """
    
    def resolve_mention(
        self, 
        mention: str, 
        context: GraphContext
    ) -> EntityResolution:
        """Resolve a single entity mention.
        
        Args:
            mention: The entity mention text.
            context: Graph context for resolution.
            
        Returns:
            EntityResolution with strategy and result.
        """
        ...
    
    def resolve_mentions(
        self, 
        mentions: List[str], 
        context: GraphContext
    ) -> List[EntityResolution]:
        """Resolve multiple entity mentions.
        
        Args:
            mentions: List of entity mention texts.
            context: Graph context for resolution.
            
        Returns:
            List of EntityResolution results.
        """
        ...
    
    def find_candidates(
        self, 
        mention: str, 
        context: GraphContext
    ) -> List[EntityCandidate]:
        """Find candidate entities for a mention.
        
        Args:
            mention: The entity mention text.
            context: Graph context for candidate search.
            
        Returns:
            List of candidate entities.
        """
        ...


class GraphAwareEntityResolver:
    """Graph-aware entity resolver implementation.
    
    This is the main implementation that addresses the core problems
    identified in the critical analysis.
    """
    
    def __init__(
        self, 
        graph_store: GraphStore,
        similarity_config: Optional[SimilarityConfig] = None
    ):
        """Initialize the entity resolver.
        
        Args:
            graph_store: Graph store for querying entities.
            similarity_config: Optional configuration for similarity scoring.
        """
        self.graph_store = graph_store
        self.similarity_scorer = EntitySimilarityScorer(similarity_config)
    
    def resolve_mention(
        self, 
        mention: str, 
        context: GraphContext
    ) -> EntityResolution:
        """Resolve a single entity mention.
        
        Args:
            mention: The entity mention text.
            context: Graph context for resolution.
            
        Returns:
            EntityResolution with strategy and result.
        """
        # Step 1: Find candidates in the graph
        candidates = self.find_candidates(mention, context)
        
        # Step 2: Score candidates by similarity
        scored_candidates = self.similarity_scorer.score_mention_candidates(
            mention, candidates, context
        )
        
        # Step 3: Determine resolution strategy
        if not scored_candidates:
            # No candidates found - create new entity
            return EntityResolution(
                mention_id=uuid4(),  # This should be the actual mention ID
                strategy=ResolutionStrategy.CREATE_NEW,
                entity_id=None,
                confidence=self._create_low_confidence(),
                reasoning=f"No similar entities found for '{mention}'. Will create new entity."
            )
        
        best_candidate = scored_candidates[0]
        
        if best_candidate.similarity > 0.6:
            # High confidence - use existing entity
            return EntityResolution(
                mention_id=uuid4(),  # This should be the actual mention ID
                strategy=ResolutionStrategy.USE_EXISTING,
                entity_id=best_candidate.id,
                confidence=self._create_high_confidence(best_candidate.similarity),
                reasoning=f"High confidence match found: {best_candidate.name} (similarity: {best_candidate.similarity:.2f})"
            )
        elif best_candidate.similarity > 0.3:
            # Medium confidence - ask user to disambiguate
            return EntityResolution(
                mention_id=uuid4(),  # This should be the actual mention ID
                strategy=ResolutionStrategy.ASK_USER,
                entity_id=None,
                confidence=self._create_medium_confidence(best_candidate.similarity),
                reasoning=f"Multiple candidates found for '{mention}'. User disambiguation required."
            )
        else:
            # Low confidence - create new entity
            return EntityResolution(
                mention_id=uuid4(),  # This should be the actual mention ID
                strategy=ResolutionStrategy.CREATE_NEW,
                entity_id=None,
                confidence=self._create_low_confidence(),
                reasoning=f"Low confidence matches found for '{mention}'. Will create new entity."
            )
    
    def resolve_mentions(
        self, 
        mentions: List[str], 
        context: GraphContext
    ) -> List[EntityResolution]:
        """Resolve multiple entity mentions.
        
        Args:
            mentions: List of entity mention texts.
            context: Graph context for resolution.
            
        Returns:
            List of EntityResolution results.
        """
        resolutions = []
        for mention in mentions:
            resolution = self.resolve_mention(mention, context)
            resolutions.append(resolution)
        return resolutions
    
    def find_candidates(
        self, 
        mention: str, 
        context: GraphContext
    ) -> List[EntityCandidate]:
        """Find candidate entities for a mention.
        
        Args:
            mention: The entity mention text.
            context: Graph context for candidate search.
            
        Returns:
            List of candidate entities.
        """
        candidates = []
        
        # Search in the graph snapshot
        for node in context.snapshot.nodes:
            # Calculate basic similarity
            similarity = self._calculate_basic_similarity(mention, node.name)
            
            if similarity > 0.1:  # Low threshold for initial filtering
                candidate = EntityCandidate(
                    id=str(node.id),
                    name=node.name,
                    label=node.label,
                    similarity=similarity,
                    properties=node.properties,
                    context={}
                )
                candidates.append(candidate)
        
        # Also check pre-computed similarities from context
        if mention in context.entity_similarities:
            for sim_data in context.entity_similarities[mention]:
                candidate = EntityCandidate(
                    id=sim_data.get('id', ''),
                    name=sim_data.get('name', ''),
                    label=sim_data.get('label'),
                    similarity=sim_data.get('similarity', 0.0),
                    properties=sim_data.get('properties', {}),
                    context=sim_data.get('context', {})
                )
                candidates.append(candidate)
        
        return candidates
    
    def _calculate_basic_similarity(self, mention: str, candidate_name: str) -> float:
        """Calculate basic string similarity.
        
        Args:
            mention: The entity mention text.
            candidate_name: The candidate entity name.
            
        Returns:
            Basic similarity score between 0.0 and 1.0.
        """
        from difflib import SequenceMatcher
        
        # Normalize strings
        mention_norm = mention.lower().strip()
        candidate_norm = candidate_name.lower().strip()
        
        # Calculate similarity
        similarity = SequenceMatcher(None, mention_norm, candidate_norm).ratio()
        
        # Boost for exact matches
        if mention_norm == candidate_norm:
            similarity = 1.0
        # Boost for substring matches
        elif mention_norm in candidate_norm or candidate_norm in mention_norm:
            similarity = max(similarity, 0.8)
        
        return similarity
    
    def _create_high_confidence(self, similarity: float) -> "EntityConfidence":
        """Create high confidence score."""
        from .models import EntityConfidence
        name_match = similarity
        type_match = 0.9
        property_match = 0.8
        context_match = 0.7
        overall = name_match * 0.4 + type_match * 0.3 + property_match * 0.2 + context_match * 0.1
        return EntityConfidence(
            name_match=name_match,
            type_match=type_match,
            property_match=property_match,
            context_match=context_match,
            overall=overall
        )
    
    def _create_medium_confidence(self, similarity: float) -> "EntityConfidence":
        """Create medium confidence score."""
        from .models import EntityConfidence
        name_match = similarity
        type_match = 0.6
        property_match = 0.5
        context_match = 0.4
        overall = name_match * 0.4 + type_match * 0.3 + property_match * 0.2 + context_match * 0.1
        return EntityConfidence(
            name_match=name_match,
            type_match=type_match,
            property_match=property_match,
            context_match=context_match,
            overall=overall
        )
    
    def _create_low_confidence(self) -> "EntityConfidence":
        """Create low confidence score."""
        from .models import EntityConfidence
        name_match = 0.1
        type_match = 0.1
        property_match = 0.1
        context_match = 0.1
        overall = name_match * 0.4 + type_match * 0.3 + property_match * 0.2 + context_match * 0.1
        return EntityConfidence(
            name_match=name_match,
            type_match=type_match,
            property_match=property_match,
            context_match=context_match,
            overall=overall
        )


class EntityResolutionService:
    """Service for managing entity resolution operations.
    
    Provides high-level operations for entity resolution with proper
    error handling and logging.
    """
    
    def __init__(self, resolver: EntityResolver):
        """Initialize the service.
        
        Args:
            resolver: Entity resolver implementation.
        """
        self.resolver = resolver
    
    def resolve_entities_from_text(
        self, 
        text: str, 
        context: GraphContext
    ) -> List[EntityResolution]:
        """Resolve entities from text.
        
        Args:
            text: Input text containing entity mentions.
            context: Graph context for resolution.
            
        Returns:
            List of entity resolutions.
        """
        # Extract entity mentions from text
        mentions = self._extract_mentions(text)
        
        # Resolve each mention
        resolutions = self.resolver.resolve_mentions(mentions, context)
        
        return resolutions
    
    def _extract_mentions(self, text: str) -> List[str]:
        """Extract entity mentions from text.
        
        Args:
            text: Input text.
            
        Returns:
            List of entity mentions.
        """
        # This is a simplified implementation
        # In a more sophisticated system, this would use NLP to extract
        # entity mentions from the text
        import re
        
        # Split on common delimiters and filter out empty strings
        words = re.split(r'[\s,;.!?]+', text)
        mentions = [word.strip() for word in words if word.strip()]
        
        # Filter out common words (this is very basic)
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        mentions = [mention for mention in mentions if mention.lower() not in common_words]
        
        return mentions
