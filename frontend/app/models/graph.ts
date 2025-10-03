/**
 * TypeScript models for graph data structures.
 * 
 * These models define the structure of nodes and edges in the graph store,
 * ensuring type safety when working with graph data in the frontend.
 */

export interface GraphNode {
  /** Unique identifier for the node */
  id: string;
  /** Node label/type (e.g., 'Person', 'Company', 'Project') */
  label: string;
  /** Natural key for the node */
  key: string;
  /** Additional properties of the node */
  properties: Record<string, any>;
  /** Timestamp when the node was created */
  created_at?: string;
  /** Timestamp when the node was last updated */
  updated_at?: string;
}

export interface GraphEdge {
  /** Unique identifier for the edge */
  id: string;
  /** Relationship type (e.g., 'DEPENDS_ON', 'WORKS_FOR', 'BELONGS_TO') */
  relationship_type: string;
  /** Source node ID */
  source_id: string;
  /** Target node ID */
  target_id: string;
  /** Source node key */
  source_key: string;
  /** Target node key */
  target_key: string;
  /** Source node label */
  source_label: string;
  /** Target node label */
  target_label: string;
  /** Additional properties of the edge */
  properties: Record<string, any>;
  /** Timestamp when the edge was created */
  created_at?: string;
  /** Timestamp when the edge was last updated */
  updated_at?: string;
}

export interface GraphData {
  /** Array of nodes in the graph */
  nodes: GraphNode[];
  /** Array of edges in the graph */
  edges: GraphEdge[];
}

export interface SubgraphData {
  /** Array of nodes in the subgraph */
  nodes: GraphNode[];
  /** Array of edges in the subgraph */
  edges: GraphEdge[];
  /** Maximum depth of relationships included */
  depth: number;
  /** IDs of central nodes used for the subgraph */
  central_nodes: string[];
}

export interface GraphElement {
  /** Type of element ('node' or 'edge') */
  type: 'node' | 'edge';
  /** Element data */
  data: GraphNode | GraphEdge;
}

export interface GraphElementProperties {
  /** Property key */
  key: string;
  /** Property value */
  value: any;
  /** Type of the value */
  type: string;
}

export interface GraphVisualizationConfig {
  /** Whether to show node labels */
  showNodeLabels: boolean;
  /** Whether to show edge labels */
  showEdgeLabels: boolean;
  /** Layout algorithm to use */
  layout: 'dagre' | 'circle' | 'grid' | 'breadthfirst';
  /** Whether to enable node selection */
  enableSelection: boolean;
  /** Whether to enable zoom and pan */
  enableZoomPan: boolean;
}
