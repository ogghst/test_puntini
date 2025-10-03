/**
 * AttributeTable component for displaying graph element properties.
 * 
 * Shows the properties of selected nodes or edges in a structured table format.
 * Provides detailed information about the selected graph element.
 */

import { Table, type TableColumn } from '../ui/table';
import type { GraphNode, GraphEdge, GraphElementProperties } from '../../models/graph';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';

export interface AttributeTableProps {
  /** Selected graph element (node or edge) */
  selectedElement?: GraphNode | GraphEdge;
  /** Element type */
  elementType?: 'node' | 'edge';
  /** Optional class name */
  className?: string;
}

export function AttributeTable({ 
  selectedElement, 
  elementType, 
  className 
}: AttributeTableProps) {
  // Convert element properties to table format
  const properties: GraphElementProperties[] = selectedElement 
    ? Object.entries(selectedElement.properties || {}).map(([key, value]) => ({
        key,
        value: value === null || value === undefined ? 'null' : String(value),
        type: typeof value,
      }))
    : [];

  // Add metadata properties
  const metadataProperties: GraphElementProperties[] = selectedElement ? [
    { key: 'id', value: selectedElement.id, type: 'string' },
    ...(elementType === 'node' 
      ? [
          { key: 'label', value: (selectedElement as GraphNode).label, type: 'string' },
          { key: 'key', value: (selectedElement as GraphNode).key, type: 'string' },
        ]
      : [
          { key: 'relationship_type', value: (selectedElement as GraphEdge).relationship_type, type: 'string' },
          { key: 'source_id', value: (selectedElement as GraphEdge).source_id, type: 'string' },
          { key: 'target_id', value: (selectedElement as GraphEdge).target_id, type: 'string' },
          { key: 'source_key', value: (selectedElement as GraphEdge).source_key, type: 'string' },
          { key: 'target_key', value: (selectedElement as GraphEdge).target_key, type: 'string' },
          { key: 'source_label', value: (selectedElement as GraphEdge).source_label, type: 'string' },
          { key: 'target_label', value: (selectedElement as GraphEdge).target_label, type: 'string' },
        ]
    ),
    ...(selectedElement.created_at ? [{ key: 'created_at', value: selectedElement.created_at, type: 'string' }] : []),
    ...(selectedElement.updated_at ? [{ key: 'updated_at', value: selectedElement.updated_at, type: 'string' }] : []),
  ] : [];

  const allProperties = [...metadataProperties, ...properties];

  const columns: TableColumn<GraphElementProperties>[] = [
    {
      key: 'key',
      header: 'Property',
      accessor: (row) => row.key,
      render: (value) => (
        <code className="text-sm font-mono bg-gray-100 px-2 py-1 rounded">
          {value}
        </code>
      ),
      width: '30%',
    },
    {
      key: 'value',
      header: 'Value',
      accessor: (row) => row.value,
      render: (value, row) => {
        // Handle different value types with appropriate formatting
        if (row.type === 'boolean') {
          return (
            <Badge variant={value === 'true' ? 'default' : 'secondary'}>
              {value}
            </Badge>
          );
        }
        
        if (row.type === 'number') {
          return <span className="font-mono">{value}</span>;
        }
        
        if (row.type === 'object' || row.type === 'array') {
          return (
            <pre className="text-xs bg-gray-100 p-2 rounded overflow-x-auto max-w-xs">
              {JSON.stringify(JSON.parse(value), null, 2)}
            </pre>
          );
        }
        
        return <span className="break-words">{value}</span>;
      },
      width: '50%',
    },
    {
      key: 'type',
      header: 'Type',
      accessor: (row) => row.type,
      render: (value) => (
        <Badge variant="outline" className="text-xs">
          {value}
        </Badge>
      ),
      width: '20%',
    },
  ];

  if (!selectedElement) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="text-lg">Element Properties</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-gray-500">
            <p>Click on a node or edge to view its properties</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          {elementType === 'node' ? 'Node' : 'Edge'} Properties
          <Badge variant="secondary">
            {elementType}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Table
          data={allProperties}
          columns={columns}
          emptyMessage="No properties available"
          size="sm"
        />
      </CardContent>
    </Card>
  );
}

export default AttributeTable;
