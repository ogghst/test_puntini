/**
 * Graph visualization component using Cytoscape.js.
 * 
 * Provides an interactive graph visualization with features for exploring nodes and edges.
 * Supports clicking on elements to view their properties and various layout options.
 */

import React, { useEffect, useRef, useState } from 'react';
import cytoscape from 'cytoscape';
// @ts-expect-error - cytoscape-dagre doesn't have TypeScript definitions
import dagre from 'cytoscape-dagre';
import type { GraphNode, GraphEdge, GraphData, GraphVisualizationConfig } from '../../models/graph';
import { AttributeTable } from './AttributeTable';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { RefreshCw, Layout, ZoomIn, ZoomOut, RotateCcw } from 'lucide-react';

// Register Cytoscape extensions
cytoscape.use(dagre);

export interface GraphProps {
  /** Graph data to visualize */
  data?: GraphData;
  /** Whether the graph is loading */
  loading?: boolean;
  /** Error message if graph loading failed */
  error?: string;
  /** Function to load graph data */
  onLoadGraph?: () => void;
  /** Optional class name */
  className?: string;
  /** Graph visualization configuration */
  config?: Partial<GraphVisualizationConfig>;
}

export function Graph({
  data,
  loading = false,
  error,
  onLoadGraph,
  className,
  config = {},
}: GraphProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<any>(null);
  const [selectedElement, setSelectedElement] = useState<GraphNode | GraphEdge | null>(null);
  const [elementType, setElementType] = useState<'node' | 'edge' | null>(null);
  
  // Use ref to store current data for event listeners
  const dataRef = useRef<GraphData | undefined>(data);
  
  // Update data ref when data changes
  useEffect(() => {
    dataRef.current = data;
  }, [data]);

  // Merge default config with provided config
  const graphConfig: GraphVisualizationConfig = {
    showNodeLabels: true,
    showEdgeLabels: true,
    layout: 'dagre',
    enableSelection: true,
    enableZoomPan: true,
    ...config,
  };

  // Initialize Cytoscape instance (only once)
  useEffect(() => {
    if (!containerRef.current || cyRef.current) return;

    // Register dagre layout
    cytoscape.use(dagre);

    cyRef.current = cytoscape({
      container: containerRef.current,
      elements: [],
      style: [
        {
          selector: 'node',
          style: {
            'background-color': '#4f46e5',
            'label': 'data(label)',
            'text-valign': 'center',
            'text-halign': 'center',
            'color': '#ffffff',
            'font-size': '12px',
            'font-weight': 'bold',
            'width': '40px',
            'height': '40px',
            'border-width': 2,
            'border-color': '#ffffff',
          },
        },
        {
          selector: 'node:selected',
          style: {
            'background-color': '#dc2626',
            'border-color': '#dc2626',
            'border-width': 3,
          },
        },
        {
          selector: 'edge',
          style: {
            'width': 2,
            'line-color': '#6b7280',
            'target-arrow-color': '#6b7280',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'label': 'data(relationship_type)',
            'font-size': '10px',
            'text-rotation': 'autorotate',
            'text-margin-y': -10,
          },
        },
        {
          selector: 'edge:selected',
          style: {
            'line-color': '#dc2626',
            'target-arrow-color': '#dc2626',
            'width': 3,
          },
        },
      ],
      userZoomingEnabled: true,
      userPanningEnabled: true,
      boxSelectionEnabled: false,
      selectionType: 'single',
    });

    // Add event listeners (these don't change)
    cyRef.current.on('tap', 'node', (event: any) => {
      const node = event.target;
      const nodeData = node.data();
      
      // Find the corresponding GraphNode from current data
      const graphNode = dataRef.current?.nodes.find(n => n.id === nodeData.id);
      if (graphNode) {
        setSelectedElement(graphNode);
        setElementType('node');
      }
    });

    cyRef.current.on('tap', 'edge', (event: any) => {
      const edge = event.target;
      const edgeData = edge.data();
      
      // Find the corresponding GraphEdge from current data
      const graphEdge = dataRef.current?.edges.find(e => e.id === edgeData.id);
      if (graphEdge) {
        setSelectedElement(graphEdge);
        setElementType('edge');
      }
    });

    // Clear selection when clicking on empty space
    cyRef.current.on('tap', (event: any) => {
      if (event.target === cyRef.current) {
        setSelectedElement(null);
        setElementType(null);
      }
    });

    // Cleanup function
    return () => {
      if (cyRef.current) {
        cyRef.current.destroy();
        cyRef.current = null;
      }
    };
  }, []); // Empty dependency array - only run once on mount

  // Update graph data when it changes
  useEffect(() => {
    if (!cyRef.current || !data) return;

    // Convert graph data to Cytoscape format
    const elements = [
      ...data.nodes.map(node => ({
        data: {
          id: node.id,
          label: node.label,
          key: node.key,
          ...node.properties,
        },
        group: 'nodes',
      })),
      ...data.edges.map(edge => ({
        data: {
          id: edge.id,
          source: edge.source_id,
          target: edge.target_id,
          relationship_type: edge.relationship_type,
          ...edge.properties,
        },
        group: 'edges',
      })),
    ];

    cyRef.current.elements().remove();
    cyRef.current.add(elements);
    cyRef.current.layout({
      name: graphConfig.layout,
      padding: 20,
      animate: true,
      animationDuration: 500,
      ...(graphConfig.layout === 'dagre' && {
        rankDir: 'TB',
        spacingFactor: 1.5,
      }),
    }).run();
  }, [data, graphConfig.layout]);


  // Layout functions
  const applyLayout = (layoutName: string) => {
    if (!cyRef.current) return;

    cyRef.current.layout({
      name: layoutName,
      padding: 20,
      animate: true,
      animationDuration: 500,
      ...(layoutName === 'dagre' && {
        rankDir: 'TB',
        spacingFactor: 1.5,
      }),
    }).run();
  };

  const zoomIn = () => {
    if (!cyRef.current) return;
    cyRef.current.zoom(cyRef.current.zoom() * 1.2);
  };

  const zoomOut = () => {
    if (!cyRef.current) return;
    cyRef.current.zoom(cyRef.current.zoom() * 0.8);
  };

  const fitToView = () => {
    if (!cyRef.current) return;
    cyRef.current.fit(undefined, 20);
  };

  return (
    <div className={`flex flex-col h-full ${className}`}>
      {/* Graph Controls */}
      <Card className="mb-4">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Graph Visualization</span>
            <div className="flex gap-2">
              <Button
                onClick={onLoadGraph}
                disabled={loading}
                size="sm"
                variant="outline"
              >
                <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                Load Graph
              </Button>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            <Button onClick={zoomIn} size="sm" variant="outline">
              <ZoomIn className="h-4 w-4" />
            </Button>
            <Button onClick={zoomOut} size="sm" variant="outline">
              <ZoomOut className="h-4 w-4" />
            </Button>
            <Button onClick={fitToView} size="sm" variant="outline">
              <RotateCcw className="h-4 w-4" />
            </Button>
            <div className="flex gap-1">
              <Button
                onClick={() => applyLayout('dagre')}
                size="sm"
                variant={graphConfig.layout === 'dagre' ? 'default' : 'outline'}
              >
                <Layout className="h-4 w-4 mr-1" />
                Dagre
              </Button>
              <Button
                onClick={() => applyLayout('circle')}
                size="sm"
                variant={graphConfig.layout === 'circle' ? 'default' : 'outline'}
              >
                <Layout className="h-4 w-4 mr-1" />
                Circle
              </Button>
              <Button
                onClick={() => applyLayout('grid')}
                size="sm"
                variant={graphConfig.layout === 'grid' ? 'default' : 'outline'}
              >
                <Layout className="h-4 w-4 mr-1" />
                Grid
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Content */}
      <div className="flex-1 flex gap-4 min-h-0">
        {/* Graph Visualization */}
        <Card className="flex-1">
          <CardContent className="p-0 h-full">
            {error ? (
              <div className="flex items-center justify-center h-full text-red-600">
                <div className="text-center">
                  <p className="font-medium">Error loading graph</p>
                  <p className="text-sm mt-1">{error}</p>
                  <Button onClick={onLoadGraph} className="mt-4" variant="outline">
                    Retry
                  </Button>
                </div>
              </div>
            ) : (
              <div
                ref={containerRef}
                className="w-full h-full min-h-[400px] bg-gray-50"
                style={{ minHeight: '400px' }}
              />
            )}
          </CardContent>
        </Card>

        {/* Properties Panel */}
        <div className="w-80 flex-shrink-0">
          <AttributeTable
            selectedElement={selectedElement || undefined}
            elementType={elementType || undefined}
            className="h-full"
          />
        </div>
      </div>

      {/* Graph Statistics */}
      {data && (
        <Card className="mt-4">
          <CardContent className="py-3">
            <div className="flex justify-between text-sm text-gray-600">
              <span>Nodes: {data.nodes.length}</span>
              <span>Edges: {data.edges.length}</span>
              <span>
                Selected: {selectedElement ? `${elementType} (${selectedElement.id})` : 'None'}
              </span>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default Graph;
