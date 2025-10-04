"""Entity similarity scoring for graph-aware entity resolution.

This module provides similarity scoring capabilities that address the
meaningless confidence scores in the current system by implementing
proper similarity calculation based on graph context.
"""

import re
from typing import Any, Dict, List, Optional
from difflib import SequenceMatcher

from pydantic import BaseModel, Field

from .models import EntityConfidence, EntityCandidate
from .context import GraphContext


class SimilarityConfig(BaseModel):
    """Configuration for similarity scoring."""
    name_weight: float = Field(default=0.4, description="Weight for name similarity")
    type_weight: float = Field(default=0.3, description="Weight for type similarity")
    property_weight: float = Field(default=0.2, description="Weight for property similarity")
    context_weight: float = Field(default=0.1, description="Weight for context similarity")
    min_similarity_threshold: float = Field(default=0.3, description="Minimum similarity to consider")
    max_candidates: int = Field(default=10, description="Maximum number of candidates to return")


class EntitySimilarityScorer:
    """Scores similarity between entity mentions and graph entities.
    
    Implements proper similarity calculation based on:
    - String similarity to existing entities
    - Property overlap with candidates
    - Context from surrounding entities
    - Type compatibility
    """
    
    def __init__(self, config: Optional[SimilarityConfig] = None):
        """Initialize the similarity scorer.
        
        Args:
            config: Optional configuration for similarity scoring.
        """
        self.config = config or SimilarityConfig()
    
    def score_mention_candidates(
        self, 
        mention: str, 
        candidates: List[EntityCandidate],
        context: GraphContext
    ) -> List[EntityCandidate]:
        """Score and rank candidates for an entity mention.
        
        Args:
            mention: The entity mention text.
            candidates: List of potential candidates.
            context: Graph context for scoring.
            
        Returns:
            List of candidates sorted by similarity score (highest first).
        """
        scored_candidates = []
        
        for candidate in candidates:
            confidence = self._calculate_confidence(mention, candidate, context)
            # Update the candidate with the calculated similarity
            candidate.similarity = confidence.overall
            scored_candidates.append(candidate)
        
        # Sort by similarity score (highest first)
        scored_candidates.sort(key=lambda c: c.similarity, reverse=True)
        
        # Filter by threshold and limit results
        filtered_candidates = [
            c for c in scored_candidates 
            if c.similarity >= self.config.min_similarity_threshold
        ]
        
        return filtered_candidates[:self.config.max_candidates]
    
    def _calculate_confidence(
        self, 
        mention: str, 
        candidate: EntityCandidate,
        context: GraphContext
    ) -> EntityConfidence:
        """Calculate confidence scores for a candidate.
        
        Args:
            mention: The entity mention text.
            candidate: The candidate entity.
            context: Graph context for scoring.
            
        Returns:
            EntityConfidence with calculated scores.
        """
        # Calculate name similarity
        name_match = self._calculate_name_similarity(mention, candidate.name)
        
        # Calculate type similarity
        type_match = self._calculate_type_similarity(mention, candidate, context)
        
        # Calculate property similarity
        property_match = self._calculate_property_similarity(mention, candidate, context)
        
        # Calculate context similarity
        context_match = self._calculate_context_similarity(mention, candidate, context)
        
        # Calculate overall weighted score
        overall = (
            name_match * self.config.name_weight +
            type_match * self.config.type_weight +
            property_match * self.config.property_weight +
            context_match * self.config.context_weight
        )
        
        return EntityConfidence(
            name_match=name_match,
            type_match=type_match,
            property_match=property_match,
            context_match=context_match,
            overall=overall
        )
    
    def _calculate_name_similarity(self, mention: str, candidate_name: str) -> float:
        """Calculate string similarity between mention and candidate name.
        
        Args:
            mention: The entity mention text.
            candidate_name: The candidate entity name.
            
        Returns:
            Similarity score between 0.0 and 1.0.
        """
        # Normalize strings for comparison
        mention_norm = self._normalize_string(mention)
        candidate_norm = self._normalize_string(candidate_name)
        
        # Use SequenceMatcher for string similarity
        similarity = SequenceMatcher(None, mention_norm, candidate_norm).ratio()
        
        # Boost score for exact matches
        if mention_norm == candidate_norm:
            similarity = 1.0
        # Boost score for substring matches
        elif mention_norm in candidate_norm or candidate_norm in mention_norm:
            similarity = max(similarity, 0.8)
        
        return similarity
    
    def _calculate_type_similarity(
        self, 
        mention: str, 
        candidate: EntityCandidate,
        context: GraphContext
    ) -> float:
        """Calculate type compatibility score.
        
        Args:
            mention: The entity mention text.
            candidate: The candidate entity.
            context: Graph context for scoring.
            
        Returns:
            Type similarity score between 0.0 and 1.0.
        """
        # For now, return a base score based on whether the candidate has a label
        # In a more sophisticated implementation, this would analyze the mention
        # to determine expected type and compare with candidate's type
        if candidate.label:
            return 0.8
        return 0.5
    
    def _calculate_property_similarity(
        self, 
        mention: str, 
        candidate: EntityCandidate,
        context: GraphContext
    ) -> float:
        """Calculate property overlap score.
        
        Args:
            mention: The entity mention text.
            candidate: The candidate entity.
            context: Graph context for scoring.
            
        Returns:
            Property similarity score between 0.0 and 1.0.
        """
        if not candidate.properties:
            return 0.0
        
        # Extract potential property values from the mention
        mention_props = self._extract_properties_from_mention(mention)
        
        if not mention_props:
            return 0.5  # Neutral score if no properties can be extracted
        
        # Calculate overlap between mention properties and candidate properties
        matches = 0
        total = len(mention_props)
        
        for prop_name, prop_value in mention_props.items():
            if prop_name in candidate.properties:
                candidate_value = str(candidate.properties[prop_name])
                if self._normalize_string(str(prop_value)) == self._normalize_string(candidate_value):
                    matches += 1
        
        return matches / total if total > 0 else 0.0
    
    def _calculate_context_similarity(
        self, 
        mention: str, 
        candidate: EntityCandidate,
        context: GraphContext
    ) -> float:
        """Calculate context similarity from surrounding entities.
        
        Args:
            mention: The entity mention text.
            candidate: The candidate entity.
            context: Graph context for scoring.
            
        Returns:
            Context similarity score between 0.0 and 1.0.
        """
        # For now, return a base score
        # In a more sophisticated implementation, this would analyze
        # the surrounding context and compare with candidate's graph context
        return 0.5
    
    def _normalize_string(self, text: str) -> str:
        """Normalize string for comparison.
        
        Args:
            text: Input text to normalize.
            
        Returns:
            Normalized string.
        """
        # Convert to lowercase and remove extra whitespace
        normalized = re.sub(r'\s+', ' ', text.lower().strip())
        # Remove special characters for better matching
        normalized = re.sub(r'[^\w\s]', '', normalized)
        return normalized
    
    def _extract_properties_from_mention(self, mention: str) -> Dict[str, Any]:
        """Extract potential property values from entity mention.
        
        Args:
            mention: The entity mention text.
            
        Returns:
            Dictionary of extracted properties.
        """
        # This is a simplified implementation
        # In a more sophisticated system, this would use NLP to extract
        # structured information from the mention
        properties = {}
        
        # Look for common patterns like email addresses, IDs, etc.
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, mention)
        if emails:
            properties['email'] = emails[0]
        
        # Look for ID patterns (e.g., TICKET-123, BUG-456)
        id_pattern = r'\b[A-Z]+-\d+\b'
        ids = re.findall(id_pattern, mention)
        if ids:
            properties['id'] = ids[0]
        
        return properties
