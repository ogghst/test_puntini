"""Graph context for entity resolution.

This module provides graph context information needed for entity resolution,
addressing the lack of graph context integration in the current system.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field

from puntini.models.node import Node
from puntini.models.edge import Edge


class GraphSnapshot(BaseModel):
    """A snapshot of relevant graph data for entity resolution.
    
    Provides only the relevant subgraph needed for entity resolution,
    avoiding the information overload of passing everything through every node.
    """
    nodes: List[Node] = Field(default_factory=list, description="Relevant nodes")
    edges: List[Edge] = Field(default_factory=list, description="Relevant edges")
    context_depth: int = Field(default=1, description="Depth of context included")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When this snapshot was created")
    
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
        """Get all edges with a specific type."""
        return [edge for edge in self.edges if edge.relationship_type == edge_type]


class GraphContext(BaseModel):
    """Context information from the graph for entity resolution.
    
    This addresses the lack of graph context integration in the current system
    by providing relevant graph information to the entity resolution process.
    """
    snapshot: GraphSnapshot = Field(description="Graph snapshot for this context")
    entity_similarities: Dict[str, List[Dict[str, Any]]] = Field(
        default_factory=dict,
        description="Pre-computed similarity scores for entities"
    )
    schema_info: Dict[str, Any] = Field(
        default_factory=dict,
        description="Schema information (labels, relationship types, etc.)"
    )
    user_context: Dict[str, Any] = Field(
        default_factory=dict,
        description="User-specific context (preferences, history, etc.)"
    )
    
    def find_similar_entities(self, mention: str, threshold: float = 0.3) -> List[Dict[str, Any]]:
        """Find entities similar to the given mention."""
        entities = self.entity_similarities.get(mention, [])
        return [entity for entity in entities if entity.get("similarity", 0.0) >= threshold]
    
    def get_schema_labels(self) -> List[str]:
        """Get all available node labels from schema."""
        return self.schema_info.get("labels", [])
    
    def get_relationship_types(self) -> List[str]:
        """Get all available relationship types from schema."""
        return self.schema_info.get("relationship_types", [])
    
    def is_entity_in_context(self, entity_id: str) -> bool:
        """Check if an entity is present in the current context."""
        return self.snapshot.get_node_by_id(entity_id) is not None
