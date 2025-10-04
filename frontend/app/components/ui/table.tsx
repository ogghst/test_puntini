/**
 * Reusable table UI component.
 * 
 * Provides a consistent table interface with customizable headers, rows, and styling.
 * Supports sorting, selection, and responsive design.
 */

import React from 'react';
import { cn } from "@/lib/utils"

export interface TableColumn<T = any> {
  /** Unique key for the column */
  key: string;
  /** Display header for the column */
  header: string;
  /** Function to extract value from row data */
  accessor: (row: T) => any;
  /** Optional render function for custom cell content */
  render?: (value: any, row: T) => React.ReactNode;
  /** Column width (CSS value) */
  width?: string;
  /** Whether the column is sortable */
  sortable?: boolean;
  /** Text alignment */
  align?: 'left' | 'center' | 'right';
}

export interface TableProps<T = any> {
  /** Array of data to display */
  data: T[];
  /** Column definitions */
  columns: TableColumn<T>[];
  /** Whether to show row numbers */
  showRowNumbers?: boolean;
  /** Optional class name for the table container */
  className?: string;
  /** Optional class name for the table element */
  tableClassName?: string;
  /** Whether the table is loading */
  loading?: boolean;
  /** Message to show when no data is available */
  emptyMessage?: string;
  /** Optional selection state */
  selectedRows?: Set<string>;
  /** Function called when row selection changes */
  onRowSelect?: (rowId: string, selected: boolean) => void;
  /** Function to get row ID */
  getRowId?: (row: T) => string;
  /** Whether to show header */
  showHeader?: boolean;
  /** Table size variant */
  size?: 'sm' | 'md' | 'lg';
}

export function Table<T = any>({
  data,
  columns,
  showRowNumbers = false,
  className,
  tableClassName,
  loading = false,
  emptyMessage = "No data available",
  selectedRows = new Set(),
  onRowSelect,
  getRowId,
  showHeader = true,
  size = 'md',
}: TableProps<T>) {
  const sizeClasses = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base',
  };

  const paddingClasses = {
    sm: 'px-2 py-1',
    md: 'px-4 py-2',
    lg: 'px-6 py-3',
  };

  if (loading) {
    return (
      <div className={cn("w-full", className)}>
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded mb-2"></div>
          <div className="space-y-2">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-6 bg-gray-100 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className={cn("w-full", className)}>
        <div className="text-center py-8 text-gray-500">
          {emptyMessage}
        </div>
      </div>
    );
  }

  return (
    <div className={cn("w-full overflow-auto", className)}>
      <table className={cn(
        "w-full border-collapse",
        sizeClasses[size],
        tableClassName
      )}>
        {showHeader && (
          <thead>
            <tr className="border-b border-gray-200">
              {showRowNumbers && (
                <th className={cn(
                  "text-left font-medium text-gray-700 bg-gray-50",
                  paddingClasses[size]
                )}>
                  #
                </th>
              )}
              {columns.map((column) => (
                <th
                  key={column.key}
                  className={cn(
                    "text-left font-medium text-gray-700 bg-gray-50",
                    paddingClasses[size],
                    column.align === 'center' && 'text-center',
                    column.align === 'right' && 'text-right'
                  )}
                  style={{ width: column.width }}
                >
                  {column.header}
                </th>
              ))}
            </tr>
          </thead>
        )}
        <tbody>
          {data.map((row, index) => {
            const rowId = getRowId ? getRowId(row) : String(index);
            const isSelected = selectedRows.has(rowId);
            
            return (
              <tr
                key={rowId}
                className={cn(
                  "border-b border-gray-100 hover:bg-gray-50",
                  isSelected && "bg-blue-50"
                )}
              >
                {showRowNumbers && (
                  <td className={cn(
                    "text-gray-500",
                    paddingClasses[size]
                  )}>
                    {index + 1}
                  </td>
                )}
                {columns.map((column) => {
                  const value = column.accessor(row);
                  const content = column.render ? column.render(value, row) : value;
                  
                  return (
                    <td
                      key={column.key}
                      className={cn(
                        paddingClasses[size],
                        column.align === 'center' && 'text-center',
                        column.align === 'right' && 'text-right'
                      )}
                    >
                      {content}
                    </td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export default Table;
