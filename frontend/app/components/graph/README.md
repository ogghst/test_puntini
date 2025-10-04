# Graph Visualization Components

This directory contains the graph visualization components for the Puntini Agent frontend.

## Components

### Graph.tsx
The main graph visualization component using Cytoscape.js. Features:
- Interactive graph rendering with nodes and edges
- Multiple layout algorithms (Dagre, Circle, Grid, Breadth-first)
- Zoom, pan, and fit-to-view controls
- Click handlers for node/edge selection
- Property display integration

### GraphContainer.tsx
Container component that handles API communication:
- Fetches graph data from backend endpoints
- Manages loading states and error handling
- Handles authentication tokens
- Converts API responses to component data format

### AttributeTable.tsx
Property display component:
- Shows detailed properties of selected graph elements
- Displays both metadata and custom properties
- Type-aware formatting for different data types
- Responsive table layout

## Dependencies

- `cytoscape` - Graph visualization library
- `cytoscape-dagre` - Layout algorithm for hierarchical graphs
- `@types/cytoscape` - TypeScript definitions

## Usage

```tsx
import { GraphContainer } from './components/graph/GraphContainer';

// In your component
<GraphContainer />
```

## API Endpoints

The components expect these backend endpoints:
- `GET /graph` - Retrieve complete graph data
- `POST /graph/subgraph` - Get subgraph around specific nodes

## Features

- **Interactive Exploration**: Click on nodes or edges to view their properties
- **Multiple Layouts**: Switch between different graph layout algorithms
- **Property Inspection**: View detailed information about graph elements
- **Responsive Design**: Works on different screen sizes
- **Type Safety**: Full TypeScript support throughout

## Configuration

The graph component accepts a configuration object:

```tsx
interface GraphVisualizationConfig {
  showNodeLabels: boolean;
  showEdgeLabels: boolean;
  layout: 'dagre' | 'circle' | 'grid' | 'breadthfirst';
  enableSelection: boolean;
  enableZoomPan: boolean;
}
```
