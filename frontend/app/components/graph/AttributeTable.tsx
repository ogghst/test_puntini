import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import type { GraphNode, GraphEdge } from '@/models/graph';

interface AttributeTableProps {
  element: GraphNode | GraphEdge | null;
}

const isGraphNode = (element: GraphNode | GraphEdge): element is GraphNode => {
    return 'labels' in element;
}

const AttributeTable: React.FC<AttributeTableProps> = ({ element }) => {
  if (!element) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Attributes</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-gray-500">Select a node or edge to see its attributes.</p>
        </CardContent>
      </Card>
    );
  }

  const { id, properties } = element;
  const isNode = isGraphNode(element);

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          {isNode ? `Node: ${id}` : `Edge: ${id}`}
        </CardTitle>
        <div className="flex flex-wrap gap-2 pt-2">
            {isNode ? (
                (element as GraphNode).labels.map((label: string) => <Badge key={label} variant="secondary">{label}</Badge>)
            ) : (
                <Badge variant="secondary">{(element as GraphEdge).type}</Badge>
            )}
        </div>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Property</TableHead>
              <TableHead>Value</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {properties && Object.entries(properties).map(([key, value]) => (
              <TableRow key={key}>
                <TableCell className="font-medium">{key}</TableCell>
                <TableCell>{String(value)}</TableCell>
              </TableRow>
            ))}
            {(!properties || Object.keys(properties).length === 0) && (
                <TableRow>
                    <TableCell colSpan={2} className="text-center text-gray-500">
                        No properties for this element.
                    </TableCell>
                </TableRow>
            )}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
};

export default AttributeTable;