"""Entity resolution system for graph-aware entity recognition.

This package provides graph-aware entity resolution capabilities that address
the fundamental flaws in the current entity recognition system:

1. Graph-aware entity recognition before planning
2. Proper entity deduplication and disambiguation  
3. Progressive context disclosure (intent → graph context → entities)
4. Meaningful confidence scores based on graph similarity
5. Handling of ambiguous references with user interaction

The system implements the standard knowledge graph pipeline:
Raw Text → Entity Mentions → Entity Candidates → Entity Linking → Resolved Entities
"""

from .models import (
    EntityMention,
    EntityCandidate, 
    EntityResolution,
    EntityConfidence,
    ResolutionStrategy,
    GraphElementType,
    AmbiguityResolution,
    ResolutionStatus
)
from .resolver import EntityResolver
from .similarity import EntitySimilarityScorer
from .context import GraphContext

__all__ = [
    # Core models
    "EntityMention",
    "EntityCandidate",
    "EntityResolution", 
    "EntityConfidence",
    "ResolutionStrategy",
    "GraphElementType",
    "AmbiguityResolution",
    "ResolutionStatus",
    
    # Core components
    "EntityResolver",
    "EntitySimilarityScorer",
    "GraphContext",
]
