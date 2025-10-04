"""Entity resolution rules for graph-aware entity recognition.

This module implements the rules for entity resolution, including:
- Match by key, email, unique properties
- Merge strategies for when entities are the same
- Conflict resolution for property conflicts
"""

from typing import Any, Dict, List, Optional, Protocol
from enum import Enum

from .models import EntityCandidate, EntityMention, ResolutionStrategy, EntityResolution
from .context import GraphContext
from .similarity import EntitySimilarityScorer


class MatchRule(str, Enum):
    """Types of matching rules for entity resolution."""
    EXACT_KEY = "exact_key"           # Match by unique key (ID, email)
    SIMILAR_NAME = "similar_name"     # Match by similar name
    PROPERTY_OVERLAP = "property_overlap"  # Match by shared properties
    TYPE_COMPATIBILITY = "type_compatibility"  # Match by compatible types


class MergeStrategy(str, Enum):
    """Strategies for merging entities when duplicates are detected."""
    PRESERVE_LATEST = "preserve_latest"        # Keep most recent values
    PRESERVE_MOST_COMPLETE = "preserve_most_complete"  # Keep entities with most properties
    PRESERVE_MOST_AUTHORITATIVE = "preserve_most_authoritative"  # Keep based on source priority
    CUSTOM_MERGE = "custom_merge"              # Use custom merge function


class ConflictResolution(str, Enum):
    """Strategies for resolving property conflicts."""
    PRESERVE_LATEST = "preserve_latest"        # Keep latest value
    PRESERVE_OLDEST = "preserve_oldest"        # Keep original value
    PRESERVE_MOST_AUTHORITATIVE = "preserve_most_authoritative"  # Based on source priority
    PRESERVE_ANNOTATED = "preserve_annotated"  # Based on user annotations
    RAISE_ERROR = "raise_error"                # Raise error for manual resolution


class EntityResolutionRules(Protocol):
    """Protocol for entity resolution rules."""
    
    def match_candidates(self, mention: EntityMention, candidates: List[EntityCandidate]) -> List[EntityCandidate]:
        """Apply matching rules to filter candidates for an entity mention.
        
        Args:
            mention: The entity mention to match
            candidates: List of potential entity candidates
            
        Returns:
            Filtered list of matching candidates
        """
        ...
    
    def determine_merge_strategy(self, candidate1: EntityCandidate, candidate2: EntityCandidate) -> MergeStrategy:
        """Determine the appropriate merge strategy for two entities.
        
        Args:
            candidate1: First entity candidate
            candidate2: Second entity candidate
            
        Returns:
            Merge strategy to use
        """
        ...
    
    def resolve_property_conflict(self, prop_name: str, value1: Any, value2: Any, 
                                 source1: str, source2: str) -> Any:
        """Resolve a conflict between two property values.
        
        Args:
            prop_name: Name of the property with conflict
            value1: First value
            value2: Second value
            source1: Source of first value
            source2: Source of second value
            
        Returns:
            Resolved property value
        """
        ...


class DefaultEntityResolutionRules:
    """Default implementation of entity resolution rules."""
    
    def __init__(self, similarity_scorer: Optional[EntitySimilarityScorer] = None):
        """Initialize the entity resolution rules.
        
        Args:
            similarity_scorer: Optional similarity scorer for name/property matching
        """
        self.similarity_scorer = similarity_scorer
        self.match_thresholds = {
            MatchRule.EXACT_KEY: 1.0,
            MatchRule.SIMILAR_NAME: 0.8,
            MatchRule.PROPERTY_OVERLAP: 0.6,
            MatchRule.TYPE_COMPATIBILITY: 0.5
        }
    
    def match_candidates(self, mention: EntityMention, candidates: List[EntityCandidate]) -> List[EntityCandidate]:
        """Apply matching rules to filter candidates for an entity mention.
        
        Args:
            mention: The entity mention to match
            candidates: List of potential entity candidates
            
        Returns:
            Filtered list of matching candidates
        """
        matching_candidates = []
        mention_text = mention.surface_form.lower().strip()
        
        for candidate in candidates:
            # Apply exact key matching first (email, ID, etc.)
            exact_match = self._match_exact_key(mention_text, candidate)
            if exact_match:
                matching_candidates.append(candidate)
                continue
            
            # Apply similar name matching
            name_match_score = self._match_similar_name(mention_text, candidate)
            if name_match_score >= self.match_thresholds[MatchRule.SIMILAR_NAME]:
                matching_candidates.append(candidate)
                continue
            
            # Apply property overlap matching
            property_match_score = self._match_property_overlap(mention, candidate)
            if property_match_score >= self.match_thresholds[MatchRule.PROPERTY_OVERLAP]:
                matching_candidates.append(candidate)
                continue
            
            # Apply type compatibility matching
            type_match_score = self._match_type_compatibility(mention, candidate)
            if type_match_score >= self.match_thresholds[MatchRule.TYPE_COMPATIBILITY]:
                matching_candidates.append(candidate)
                continue
        
        return matching_candidates
    
    def _match_exact_key(self, mention_text: str, candidate: EntityCandidate) -> bool:
        """Check for exact key matches (email, ID, etc.).
        
        Args:
            mention_text: The entity mention text
            candidate: The candidate entity
            
        Returns:
            True if there's an exact key match
        """
        # Check if mention matches candidate ID
        if mention_text == candidate.id.lower().strip():
            return True
        
        # Check for email addresses in properties
        if 'email' in candidate.properties:
            email = str(candidate.properties['email']).lower().strip()
            if mention_text == email:
                return True
        
        # Check for unique keys in properties
        for prop_name, prop_value in candidate.properties.items():
            if prop_name in ['key', 'username', 'login', 'identifier', 'id']:
                if str(prop_value).lower().strip() == mention_text:
                    return True
        
        return False
    
    def _match_similar_name(self, mention_text: str, candidate: EntityCandidate) -> float:
        """Calculate similarity between mention and candidate name.
        
        Args:
            mention_text: The entity mention text
            candidate: The candidate entity
            
        Returns:
            Similarity score between 0 and 1
        """
        if not self.similarity_scorer:
            # Simple similarity calculation if no scorer provided
            candidate_name = candidate.name.lower().strip()
            if mention_text == candidate_name:
                return 1.0
            elif mention_text in candidate_name or candidate_name in mention_text:
                return 0.8
            else:
                # Calculate basic similarity using sequence matching
                from difflib import SequenceMatcher
                return SequenceMatcher(None, mention_text, candidate_name).ratio()
        
        # Use the similarity scorer if available
        # This is a simplified version - in real implementation, we'd call scorer
        candidate_name = candidate.name.lower().strip()
        mention_text = mention_text.strip()
        
        if mention_text == candidate_name:
            return 1.0
        elif mention_text in candidate_name or candidate_name in mention_text:
            return 0.8
        else:
            from difflib import SequenceMatcher
            return SequenceMatcher(None, mention_text, candidate_name).ratio()
    
    def _match_property_overlap(self, mention: EntityMention, candidate: EntityCandidate) -> float:
        """Calculate property overlap between mention and candidate.
        
        Args:
            mention: The entity mention
            candidate: The candidate entity
            
        Returns:
            Overlap score between 0 and 1
        """
        # This is a simplified version - in practice, you'd need to extract potential
        # properties from the mention text and compare with candidate properties
        overlap_count = 0
        total_mention_properties = 0
        
        # Extract potential properties from mention context
        # This is a simplified approach - in practice, you'd use NLP to extract properties
        mention_context = mention.context
        if not mention_context:
            return 0.0
        
        # Look for properties in candidate that match values in mention context
        for key, value in mention_context.items():
            if key in candidate.properties:
                candidate_value = str(candidate.properties[key]).lower()
                if str(value).lower() in candidate_value or candidate_value in str(value).lower():
                    overlap_count += 1
            # Also check if mention value matches any candidate property value
            for prop_key, prop_value in candidate.properties.items():
                if str(value).lower() == str(prop_value).lower():
                    overlap_count += 1
        
        if hasattr(mention_context, '__len__'):
            total_mention_properties = len([k for k in mention_context.keys() if k != 'sentence'])
        else:
            total_mention_properties = len(mention_context) if isinstance(mention_context, dict) else 0
        
        return overlap_count / total_mention_properties if total_mention_properties > 0 else 0.0
    
    def _match_type_compatibility(self, mention: EntityMention, candidate: EntityCandidate) -> float:
        """Check type compatibility between mention and candidate.
        
        Args:
            mention: The entity mention
            candidate: The candidate entity
            
        Returns:
            Compatibility score between 0 and 1
        """
        # Check if mention element type is compatible with candidate type
        # This could be enhanced to check semantic compatibility
        mention_type = getattr(mention, 'element_type', None)
        candidate_label = candidate.label
        
        if not mention_type or not candidate_label:
            return 0.5  # Neutral score if no type info available
        
        # Basic type compatibility check
        mention_type_str = mention_type.value if hasattr(mention_type, 'value') else str(mention_type)
        candidate_label_str = candidate_label.lower() if candidate_label else ''
        
        if mention_type_str in candidate_label_str or candidate_label_str in mention_type_str:
            return 1.0
        
        return 0.5  # Partial compatibility for unknown combinations
    
    def determine_merge_strategy(self, candidate1: EntityCandidate, candidate2: EntityCandidate) -> MergeStrategy:
        """Determine the appropriate merge strategy for two entities.
        
        Args:
            candidate1: First entity candidate
            candidate2: Second entity candidate
            
        Returns:
            Merge strategy to use
        """
        # For now, return the default strategy
        # In a more sophisticated system, this would consider:
        # - data source quality
        # - update timestamps
        # - completeness of information
        # - user preferences
        return MergeStrategy.PRESERVE_MOST_COMPLETE
    
    def resolve_property_conflict(self, prop_name: str, value1: Any, value2: Any, 
                                 source1: str = "unknown", source2: str = "unknown") -> Any:
        """Resolve a conflict between two property values.
        
        Args:
            prop_name: Name of the property with conflict
            value1: First value
            value2: Second value
            source1: Source of first value
            source2: Source of second value
            
        Returns:
            Resolved property value
        """
        # Default resolution strategy - preserve the most recently updated
        # In practice, this could be configurable per property type
        if prop_name in ['email', 'id', 'key'] and str(value1).lower() == str(value2).lower():
            # For unique identifiers that are equal, just return one
            return value1
        elif prop_name in ['email', 'id', 'key']:
            # For unique identifiers that are different, this is a real conflict
            # In practice, you might want to raise an error or ask for human input
            return value1  # Default to first value
        else:
            # For non-unique properties, return the more complete/authoritative value
            # This is a simplified strategy - could be enhanced based on many factors
            if len(str(value1)) >= len(str(value2)):
                return value1
            else:
                return value2


class EntityDeduplicationEngine:
    """Engine for handling entity deduplication based on resolution rules."""
    
    def __init__(self, rules: EntityResolutionRules):
        """Initialize the deduplication engine.
        
        Args:
            rules: Entity resolution rules implementation
        """
        self.rules = rules
    
    def find_duplicates(self, candidates: List[EntityCandidate], 
                       threshold: float = 0.8) -> List[List[EntityCandidate]]:
        """Find potential duplicate entities among candidates.
        
        Args:
            candidates: List of entity candidates to check for duplicates
            threshold: Similarity threshold for considering duplicates
            
        Returns:
            List of groups of duplicate candidates
        """
        duplicate_groups = []
        processed = set()
        
        for i, candidate1 in enumerate(candidates):
            if candidate1.id in processed:
                continue
                
            group = [candidate1]
            processed.add(candidate1.id)
            
            for j, candidate2 in enumerate(candidates[i+1:], i+1):
                if candidate2.id in processed:
                    continue
                
                # Calculate potential similarity score between candidates
                similarity = self._calculate_candidate_similarity(candidate1, candidate2)
                if similarity >= threshold:
                    group.append(candidate2)
                    processed.add(candidate2.id)
            
            if len(group) > 1:
                duplicate_groups.append(group)
        
        return duplicate_groups
    
    def _calculate_candidate_similarity(self, candidate1: EntityCandidate, 
                                       candidate2: EntityCandidate) -> float:
        """Calculate similarity between two entity candidates.
        
        Args:
            candidate1: First candidate
            candidate2: Second candidate
            
        Returns:
            Similarity score between 0 and 1
        """
        # Calculate similarity based on name, properties, and type
        name_similarity = 0.0
        if candidate1.name and candidate2.name:
            from difflib import SequenceMatcher
            name_similarity = SequenceMatcher(
                None, 
                candidate1.name.lower().strip(), 
                candidate2.name.lower().strip()
            ).ratio()
        
        # Calculate property overlap
        prop_overlap = 0.0
        common_props = 0
        total_props = len(set(candidate1.properties.keys()) | set(candidate2.properties.keys()))
        
        for prop_key in candidate1.properties:
            if prop_key in candidate2.properties:
                common_props += 1
                if str(candidate1.properties[prop_key]).lower() == str(candidate2.properties[prop_key]).lower():
                    prop_overlap += 1
        
        prop_similarity = prop_overlap / common_props if common_props > 0 else 0.0
        total_similarity = (name_similarity * 0.7) + (prop_similarity * 0.3)  # Weighted average
        
        return total_similarity
    
    def merge_entities(self, candidates: List[EntityCandidate]) -> EntityCandidate:
        """Merge multiple entity candidates into a single entity.
        
        Args:
            candidates: List of entity candidates to merge
            
        Returns:
            Merged entity candidate
        """
        if not candidates:
            raise ValueError("Cannot merge empty list of candidates")
        
        if len(candidates) == 1:
            return candidates[0]
        
        # Use the first candidate as base and merge others into it
        base_candidate = candidates[0]
        merged_properties = base_candidate.properties.copy()
        merged_name = base_candidate.name
        merged_id = base_candidate.id
        merged_label = base_candidate.label
        merged_similarity = base_candidate.similarity
        
        for candidate in candidates[1:]:
            # Determine merge strategy
            strategy = self.rules.determine_merge_strategy(base_candidate, candidate)
            
            # Merge properties based on strategy
            for prop_name, prop_value in candidate.properties.items():
                if prop_name in merged_properties:
                    # Resolve conflict
                    resolved_value = self.rules.resolve_property_conflict(
                        prop_name, 
                        merged_properties[prop_name], 
                        prop_value
                    )
                    merged_properties[prop_name] = resolved_value
                else:
                    merged_properties[prop_name] = prop_value
            
            # Update name if better one found based on strategy
            if self._should_update_name(merged_name, candidate.name, strategy):
                merged_name = candidate.name
            
            # Update similarity (take max)
            if candidate.similarity > merged_similarity:
                merged_similarity = candidate.similarity
        
        return EntityCandidate(
            id=merged_id,
            name=merged_name,
            label=merged_label,
            similarity=merged_similarity,
            properties=merged_properties,
            context={**base_candidate.context, **{k: v for c in candidates[1:] for k, v in c.context.items()}}
        )
    
    def _should_update_name(self, current_name: str, new_name: str, strategy: MergeStrategy) -> bool:
        """Determine if the name should be updated based on merge strategy.
        
        Args:
            current_name: Current name
            new_name: New name to potentially use
            strategy: Merge strategy
            
        Returns:
            True if name should be updated
        """
        if strategy == MergeStrategy.PRESERVE_MOST_COMPLETE:
            # Update if new name is longer (more complete)
            return len(new_name) > len(current_name)
        elif strategy == MergeStrategy.PRESERVE_LATEST:
            # In this simplified version, we don't have timestamps
            # So we'll update to the new name
            return True
        else:
            return False