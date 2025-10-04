"""Graph context management for the agent system.

This module provides relevant graph subgraphs to nodes that need them,
implementing the graph context integration planned in Phase 5 of the
refactoring plan. It focuses on providing graph snapshots, entity similarity
queries, and context-aware entity matching.

Based on the refactoring plan: Provide relevant graph subgraphs to nodes that need them
Features: Graph snapshot creation, entity similarity queries, context-aware entity matching
"""

from typing import Any, Dict, List, Optional, Set
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from ..models.node import Node
from ..models.edge import Edge
from ..interfaces.graph_store import GraphStore
from ..entity_resolution.models import EntityMention, EntityCandidate
from ..entity_resolution.similarity import EntitySimilarityScorer
from ..entity_resolution.context import GraphContext, GraphSnapshot


class SubgraphQuery(BaseModel):
    """Specification for querying relevant subgraphs from the graph store."""
    
    node_types: List[str] = Field(default_factory=list, description="Node types to include in subgraph")
    relationship_types: List[str] = Field(default_factory=list, description="Relationship types to include")
    max_depth: int = Field(default=2, description="Maximum depth of relationships to traverse")
    max_nodes: int = Field(default=50, description="Maximum number of nodes to include")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Filters for node/edge selection")
    include_properties: bool = Field(default=True, description="Whether to include node/edge properties")


class GraphSubgraph(BaseModel):
    """A subgraph extracted from the main graph store."""
    
    nodes: List[Node] = Field(default_factory=list, description="Nodes in the subgraph")
    edges: List[Edge] = Field(default_factory=list, description="Edges in the subgraph")
    query_spec: Optional[SubgraphQuery] = Field(default=None, description="Query specification used to create this subgraph")
    query_time: datetime = Field(default_factory=datetime.utcnow, description="When this subgraph was created")
    context_depth: int = Field(default=1, description="Depth of relationships included")
    
    def get_node_by_id(self, node_id: str) -> Optional[Node]:
        """Get a node by its ID."""
        for node in self.nodes:
            if str(node.id) == node_id:
                return node
        return None
    
    def get_nodes_by_label(self, label: str) -> List[Node]:
        """Get all nodes with a specific label."""
        return [node for node in self.nodes if node.label == label]
    
    def get_edges_by_type(self, edge_type: str) -> List[Edge]:
        """Get all edges of a specific type."""
        return [edge for edge in self.edges if edge.relationship_type == edge_type]
    
    def get_neighbors(self, node_id: str) -> List[Node]:
        """Get all neighboring nodes for a given node ID."""
        neighbor_ids = set()
        
        # Find edges connected to this node
        for edge in self.edges:
            if str(edge.source_id) == node_id:
                neighbor_ids.add(str(edge.target_id))
            elif str(edge.target_id) == node_id:
                neighbor_ids.add(str(edge.source_id))
        
        # Return the corresponding nodes
        return [node for node in self.nodes if str(node.id) in neighbor_ids]


class GraphContextManager:
    """Manages graph context for the agent system."""
    
    def __init__(self, graph_store: GraphStore, similarity_scorer: Optional[EntitySimilarityScorer] = None):
        """Initialize the graph context manager.
        
        Args:
            graph_store: The graph store to query for context
            similarity_scorer: Optional similarity scorer for context-aware matching
        """
        self.graph_store = graph_store
        self.similarity_scorer = similarity_scorer
    
    def create_context_for_query(self, query_text: str) -> GraphContext:
        """Create a graph context relevant to a query.
        
        Args:
            query_text: Query text to determine relevant context for
            
        Returns:
            GraphContext with relevant subgraph and information
        """
        # Extract potential entity mentions from query text
        entity_mentions = self._extract_entity_mentions(query_text)
        
        # Create subgraph based on entity mentions
        subgraph = self._create_relevant_subgraph(entity_mentions)
        
        # Create entity similarities based on the query and subgraph
        entity_similarities = self._calculate_entity_similarities(query_text, subgraph)
        
        # Get schema information
        schema_info = self._get_schema_info()
        
        # Create the graph context
        graph_snapshot = GraphSnapshot(
            nodes=subgraph.nodes,
            edges=subgraph.edges,
            context_depth=subgraph.context_depth
        )
        
        return GraphContext(
            snapshot=graph_snapshot,
            entity_similarities=entity_similarities,
            schema_info=schema_info,
            user_context={}
        )
    
    def create_context_for_entities(self, entities: List[str], 
                                   max_depth: int = 2, 
                                   max_nodes: int = 50) -> GraphContext:
        """Create a graph context focused on specific entities.
        
        Args:
            entities: List of entity names to focus on
            max_depth: Maximum relationship depth to traverse
            max_nodes: Maximum number of nodes to include
            
        Returns:
            GraphContext with subgraph focused on specified entities
        """
        # Find nodes matching the entity names
        matching_nodes = []
        for entity_name in entities:
            nodes = self.graph_store.find_nodes_by_name(entity_name)
            matching_nodes.extend(nodes)
        
        # Get the subgraph around these nodes
        subgraph_nodes = set()
        subgraph_edges = set()
        
        for node in matching_nodes:
            # Get the node and its neighbors up to max_depth
            neighbor_subgraph = self.graph_store.get_subgraph_around_node(
                str(node.id), max_depth=max_depth, max_nodes=max_nodes
            )
            
            # Add nodes and edges to our collections
            for subgraph_node in neighbor_subgraph.nodes:
                subgraph_nodes.add(subgraph_node)
            
            for subgraph_edge in neighbor_subgraph.edges:
                subgraph_edges.add(subgraph_edge)
        
        # Create the graph context
        graph_snapshot = GraphSnapshot(
            nodes=list(subgraph_nodes),
            edges=list(subgraph_edges),
            context_depth=max_depth
        )
        
        schema_info = self._get_schema_info()
        
        return GraphContext(
            snapshot=graph_snapshot,
            entity_similarities={},  # Will be populated when needed
            schema_info=schema_info,
            user_context={}
        )
    
    def create_context_around_node(self, node_id: str, max_depth: int = 2) -> GraphContext:
        """Create a graph context around a specific node.
        
        Args:
            node_id: ID of the node to center the context around
            max_depth: Maximum relationship depth to traverse
            
        Returns:
            GraphContext with subgraph around the specified node
        """
        subgraph = self.graph_store.get_subgraph_around_node(node_id, max_depth=max_depth)
        
        graph_snapshot = GraphSnapshot(
            nodes=subgraph.nodes,
            edges=subgraph.edges,
            context_depth=max_depth
        )
        
        schema_info = self._get_schema_info()
        
        return GraphContext(
            snapshot=graph_snapshot,
            entity_similarities={},
            schema_info=schema_info,
            user_context={}
        )
    
    def query_similar_entities(self, entity_mention: EntityMention, 
                              threshold: float = 0.3) -> List[EntityCandidate]:
        """Query the graph for entities similar to the given mention.
        
        Args:
            entity_mention: The entity mention to find similar entities for
            threshold: Similarity threshold for matches
            
        Returns:
            List of similar entity candidates
        """
        # Find all nodes in the graph
        all_nodes = self.graph_store.get_all_nodes(limit=1000)  # Limit to avoid performance issues
        
        candidates = []
        for node in all_nodes:
            # Create a temporary candidate
            candidate = EntityCandidate(
                id=str(node.id),
                name=node.properties.get('name', node.key),  # Use name from properties or fallback to key
                label=node.label,
                similarity=0.0,  # Will be calculated
                properties=node.properties,
                context={}
            )
            candidates.append(candidate)
        
        # If we have a similarity scorer, use it to rank candidates
        if self.similarity_scorer:
            # Create a temporary graph context for scoring
            temp_context = GraphContext(
                snapshot=GraphSnapshot(nodes=all_nodes, edges=[], context_depth=1),
                entity_similarities={},
                schema_info=self._get_schema_info(),
                user_context={}
            )
            
            scored_candidates = self.similarity_scorer.score_mention_candidates(
                entity_mention.surface_form, candidates, temp_context
            )
            
            # Filter by threshold
            return [c for c in scored_candidates if c.similarity >= threshold]
        else:
            # Simple fuzzy matching without proper scoring
            from difflib import SequenceMatcher
            
            mention_text = entity_mention.surface_form.lower().strip()
            scored_candidates = []
            
            for candidate in candidates:
                similarity = SequenceMatcher(
                    None, mention_text, candidate.name.lower().strip()
                ).ratio()
                
                if similarity >= threshold:
                    candidate.similarity = similarity
                    scored_candidates.append(candidate)
            
            # Sort by similarity
            scored_candidates.sort(key=lambda c: c.similarity, reverse=True)
            return scored_candidates
    
    def _extract_entity_mentions(self, query_text: str) -> List[str]:
        """Extract potential entity mentions from query text.
        
        Args:
            query_text: Query text to extract entities from
            
        Returns:
            List of potential entity names
        """
        # This is a simplified implementation
        # In practice, you'd use NLP to extract named entities
        
        # Split by common delimiters and return potential entity names
        import re
        # Extract words that could be entity names (capitalize or with specific patterns)
        potential_entities = re.findall(r'\b[A-Z][a-z]+\b|\b[A-Z]{2,}\b|\b\w+\-\d+\b', query_text)
        
        # Remove duplicates while preserving order
        seen = set()
        result = []
        for item in potential_entities:
            item_lower = item.lower()
            if item_lower not in seen:
                seen.add(item_lower)
                result.append(item)
        
        return result
    
    def _create_relevant_subgraph(self, entity_mentions: List[str]) -> GraphSubgraph:
        """Create a subgraph relevant to the given entity mentions.
        
        Args:
            entity_mentions: List of entity names to focus on
            
        Returns:
            Relevant subgraph
        """
        all_nodes = set()
        all_edges = set()
        
        for entity_mention in entity_mentions:
            # Find nodes matching this entity mention
            nodes = self.graph_store.find_nodes_by_name(entity_mention)
            for node in nodes:
                all_nodes.add(node)
                
                # Get the subgraph around this node
                subgraph = self.graph_store.get_subgraph_around_node(str(node.id), max_depth=2)
                
                for subgraph_node in subgraph.nodes:
                    all_nodes.add(subgraph_node)
                
                for subgraph_edge in subgraph.edges:
                    all_edges.add(subgraph_edge)
        
        return GraphSubgraph(
            nodes=list(all_nodes),
            edges=list(all_edges),
            context_depth=2
        )
    
    def _calculate_entity_similarities(self, query_text: str, subgraph: GraphSubgraph) -> Dict[str, List[Dict[str, Any]]]:
        """Calculate entity similarities for context-aware matching.
        
        Args:
            query_text: Original query text
            subgraph: Subgraph to calculate similarities for
            
        Returns:
            Dictionary mapping entity names to similar entities with scores
        """
        entity_similarities = {}
        
        # For each node in the subgraph, calculate similarity to the query
        for node in subgraph.nodes:
            # Simple name similarity calculation
            from difflib import SequenceMatcher
            node_name = node.properties.get('name', node.key)
            similarity = SequenceMatcher(
                None, query_text.lower(), node_name.lower()
            ).ratio()
            
            if similarity > 0.1:  # Only include if somewhat similar
                if query_text not in entity_similarities:
                    entity_similarities[query_text] = []
                
                entity_similarities[query_text].append({
                    'id': str(node.id),
                    'name': node.properties.get('name', node.key),
                    'label': node.label,
                    'similarity': similarity,
                    'properties': node.properties,
                    'context': {}
                })
        
        return entity_similarities
    
    def _get_schema_info(self) -> Dict[str, Any]:
        """Get schema information from the graph store.
        
        Returns:
            Dictionary with schema information
        """
        try:
            labels = self.graph_store.get_all_node_labels()
            relationship_types = self.graph_store.get_all_relationship_types()
            
            return {
                'labels': labels,
                'relationship_types': relationship_types
            }
        except Exception:
            # If schema info is not available, return empty
            return {
                'labels': [],
                'relationship_types': []
            }


class ContextAwareEntityMatcher:
    """Matches entities with awareness of graph context."""
    
    def __init__(self, context_manager: GraphContextManager):
        """Initialize the context-aware entity matcher.
        
        Args:
            context_manager: Graph context manager to use for context
        """
        self.context_manager = context_manager
    
    def match_entity_to_graph(self, entity_mention: str, context: Optional[GraphContext] = None,
                             threshold: float = 0.5) -> List[EntityCandidate]:
        """Match an entity mention to existing graph entities with context awareness.
        
        Args:
            entity_mention: The entity mention to match
            context: Optional graph context (will be created if not provided)
            threshold: Similarity threshold for matches
            
        Returns:
            List of matching entity candidates
        """
        # If no context provided, create it from the entity mention
        if not context:
            temp_mention = EntityMention(surface_form=entity_mention, element_type="node_ref")
            context = self.context_manager.create_context_for_query(entity_mention)
        
        # Query for similar entities
        temp_mention = EntityMention(surface_form=entity_mention, element_type="node_ref")
        candidates = self.context_manager.query_similar_entities(temp_mention, threshold)
        
        return candidates
    
    def find_potential_duplicates(self, new_entity: Dict[str, Any], 
                                 context: Optional[GraphContext] = None,
                                 threshold: float = 0.8) -> List[EntityCandidate]:
        """Find potential duplicate entities for a new entity.
        
        Args:
            new_entity: Dictionary representing the new entity
            context: Optional graph context (will be created if not provided)
            threshold: Similarity threshold for considering duplicates
            
        Returns:
            List of potential duplicate candidates
        """
        entity_name = new_entity.get('name', new_entity.get('key', ''))
        
        if not context:
            context = self.context_manager.create_context_for_query(entity_name)
        
        # Find similar entities based on name and properties
        temp_mention = EntityMention(surface_form=entity_name, element_type="node_ref")
        similar_entities = self.context_manager.query_similar_entities(temp_mention, threshold=0.1)
        
        # Filter by higher similarity for duplicates
        potential_duplicates = [e for e in similar_entities if e.similarity >= threshold]
        
        return potential_duplicates