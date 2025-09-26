export interface GraphNode {
    id: string | number;
    labels: string[];
    properties: {
      name?: string;
      title?: string;
      [key: string]: unknown;
    };
  }

  export interface GraphEdge {
    id: string | number;
    type: string;
    start_node_id: string | number;
    end_node_id: string | number;
    properties: {
      [key: string]: unknown;
    };
  }

  export interface GraphData {
    nodes: GraphNode[];
    relationships: GraphEdge[];
  }