import React, { useEffect, useRef, useState } from 'react';
import cytoscape from 'cytoscape';
import type { Core, ElementDefinition } from 'cytoscape';
import klay from 'cytoscape-klay';
import { useSession, useMessages } from '@/utils/session';
import type { GraphData, GraphNode, GraphEdge } from '@/models/graph';

cytoscape.use(klay);

// Helper to transform backend graph data to Cytoscape format
const transformDataToCytoscape = (data: GraphData): ElementDefinition[] => {
  if (!data || (!data.nodes && !data.relationships)) {
    return [];
  }

  const nodes = (data.nodes || []).map((node: GraphNode) => ({
    group: 'nodes' as const,
    data: {
      id: String(node.id),
      label: (node.properties && (node.properties.name || node.properties.title)) || (node.labels && node.labels[0]) || String(node.id),
      ...node.properties,
      raw: node,
    },
  }));

  const edges = (data.relationships || []).map((edge: GraphEdge) => ({
    group: 'edges' as const,
    data: {
      id: String(edge.id),
      source: String(edge.start_node_id),
      target: String(edge.end_node_id),
      label: edge.type,
      ...edge.properties,
      raw: edge,
    },
  }));

  return [...nodes, ...edges];
};

interface GraphProps {
  onElementSelect: (element: GraphNode | GraphEdge | null) => void;
}

const Graph: React.FC<GraphProps> = ({ onElementSelect }) => {
  const cyRef = useRef<HTMLDivElement>(null);
  const { currentSession, createSession } = useSession();
  const { messages } = useMessages(currentSession?.session_id || null);
  const [cy, setCy] = useState<Core | null>(null);

  // Create a session if one doesn't exist
  useEffect(() => {
    if (!currentSession) {
        createSession({ user_id: 'graph_user' });
    }
  }, [currentSession, createSession]);

  // Initialize Cytoscape instance
  useEffect(() => {
    if (cyRef.current && !cy) {
      const cyInstance = cytoscape({
        container: cyRef.current,
        style: [
          {
            selector: 'node',
            style: {
              'background-color': '#38bdf8', // light-blue-400
              'label': 'data(label)',
              'color': '#ffffff',
              'text-valign': 'center',
              'text-halign': 'center',
              'font-size': '10px',
              'width': '60px',
              'height': '60px',
              'shape': 'ellipse',
              'text-wrap': 'wrap',
              'text-max-width': '50px',
              'border-width': 2,
              'border-color': '#0ea5e9' // sky-500
            },
          },
          {
            selector: 'edge',
            style: {
              'width': 2,
              'line-color': '#94a3b8', // slate-400
              'target-arrow-color': '#94a3b8',
              'target-arrow-shape': 'triangle',
              'curve-style': 'bezier',
              'label': 'data(label)',
              'font-size': '10px',
              'color': '#475569', // slate-600
              'text-background-color': '#ffffff',
              'text-background-opacity': 0.7,
              'text-background-padding': '2px',
            },
          },
          {
            selector: 'node:selected',
            style: {
              'border-width': 4,
              'border-color': '#fb923c', // orange-400
            },
          },
          {
            selector: 'edge:selected',
            style: {
              'line-color': '#fb923c',
              'target-arrow-color': '#fb923c',
              'width': 4,
            },
          },
        ],
        layout: {
          name: 'klay',
          padding: 30,
          klay: {
            direction: 'RIGHT',
            spacing: 40,
          },
        } as any,
      });
      setCy(cyInstance);
    }
  }, [cyRef, cy]);

  // Load graph data
  const loadGraphData = (graphData: GraphData) => {
    if (cy) {
      const elements = transformDataToCytoscape(graphData);
      cy.elements().remove();
      cy.add(elements);
      cy.layout({
        name: 'klay',
        padding: 30,
        klay: {
          direction: 'RIGHT',
          spacing: 40,
        },
        animate: true,
      } as any).run();
    }
  };

  // Load initial graph data from session
  useEffect(() => {
    if (cy && currentSession?.graph_data && Object.keys(currentSession.graph_data).length > 0) {
      loadGraphData(currentSession.graph_data as unknown as GraphData);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cy, currentSession]);

  // Handle graph updates from messages
  useEffect(() => {
    const graphUpdateMessage = messages.slice().reverse().find(msg => msg.type === 'graph_update');
    if (cy && graphUpdateMessage?.data) {
      loadGraphData(graphUpdateMessage.data as unknown as GraphData);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cy, messages]);

  // Handle node/edge selection and focus
  useEffect(() => {
    if (cy) {
      const handleSelect = (element: cytoscape.Singular | null) => {
        onElementSelect(element ? element.data('raw') : null);
        cy.elements().unselect();
        if (element) {
          element.select();
        }
      };

      cy.on('tap', 'node', (event) => {
        const node = event.target;
        handleSelect(node);
        cy.animate({
          fit: {
            eles: node.union(node.neighborhood()),
            padding: 50,
          },
          duration: 500,
        });
      });

      cy.on('tap', 'edge', (event) => {
        const edge = event.target;
        handleSelect(edge);
      });

      cy.on('tap', (event) => {
        if (event.target === cy) {
          handleSelect(null);
          cy.animate({
            fit: {
              eles: cy.elements(),
              padding: 50,
            },
            duration: 500,
          });
        }
      });

      return () => {
        cy.off('tap');
      };
    }
  }, [cy, onElementSelect]);

  return <div ref={cyRef} style={{ width: '100%', height: '100%' }} />;
};

export default Graph;