import Graph from '@/components/graph/Graph';
import AttributeTable from '@/components/graph/AttributeTable';
import React, { useState } from 'react';
import type { GraphNode, GraphEdge } from '@/models/graph';

const GraphPage: React.FC = () => {
  const [selectedElement, setSelectedElement] = useState<GraphNode | GraphEdge | null>(null);

  return (
    <div className="h-full flex">
      <div className="w-3/4 h-full">
        <Graph onElementSelect={setSelectedElement} />
      </div>
      <div className="w-1/4 h-full border-l p-4 overflow-auto">
        <AttributeTable element={selectedElement} />
      </div>
    </div>
  );
};

export default GraphPage;