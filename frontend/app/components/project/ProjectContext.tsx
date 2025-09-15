/**
 * Project Context Component
 *
 * Manages project context and provides interface for viewing and updating
 * project-specific information within a session.
 */

import {
  Edit3,
  FolderOpen,
  Info,
  Plus,
  RefreshCw,
  Save,
  X,
} from "lucide-react";
import React, { useCallback, useEffect, useState } from "react";
import {
  SessionAPI,
  SessionAPIError,
  type ProjectContext as ProjectContextType,
} from "../../utils/session";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Input } from "../ui/input";
import { ScrollArea } from "../ui/scroll-area";
import { Textarea } from "../ui/textarea";

interface ProjectContextProps {
  sessionId: string | null;
  onContextUpdate?: (context: Record<string, any>) => void;
}

export const ProjectContext: React.FC<ProjectContextProps> = ({
  sessionId,
  onContextUpdate,
}) => {
  const [context, setContext] = useState<ProjectContextType | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editData, setEditData] = useState<Record<string, any>>({});

  // Load project context
  const loadContext = useCallback(async () => {
    if (!sessionId) return;

    setIsLoading(true);
    setError(null);

    try {
      const contextData = await SessionAPI.getProjectContext(sessionId);
      setContext(contextData);
      setEditData(contextData.project_context);
    } catch (err) {
      const apiError =
        err instanceof SessionAPIError
          ? err
          : new SessionAPIError("Failed to load project context");
      setError(apiError.message);
    } finally {
      setIsLoading(false);
    }
  }, [sessionId]);

  // Load context on session change
  useEffect(() => {
    loadContext();
  }, [sessionId, loadContext]);

  // Save context changes
  const handleSave = async () => {
    if (!sessionId) return;

    setIsLoading(true);
    setError(null);

    try {
      await SessionAPI.updateProjectContext(sessionId, editData);
      await loadContext(); // Reload to get updated data
      setIsEditing(false);

      if (onContextUpdate) {
        onContextUpdate(editData);
      }
    } catch (err) {
      const apiError =
        err instanceof SessionAPIError
          ? err
          : new SessionAPIError("Failed to save project context");
      setError(apiError.message);
    } finally {
      setIsLoading(false);
    }
  };

  // Cancel editing
  const handleCancel = () => {
    setEditData(context?.project_context || {});
    setIsEditing(false);
  };

  // Add new context field
  const handleAddField = () => {
    const key = prompt("Enter field name:");
    if (key && !editData[key]) {
      setEditData((prev) => ({ ...prev, [key]: "" }));
    }
  };

  // Remove context field
  const handleRemoveField = (key: string) => {
    setEditData((prev) => {
      const newData = { ...prev };
      delete newData[key];
      return newData;
    });
  };

  // Update field value
  const handleFieldChange = (key: string, value: any) => {
    setEditData((prev) => ({ ...prev, [key]: value }));
  };

  // Render context field
  const renderField = (key: string, value: any) => {
    const isString = typeof value === "string";
    const isNumber = typeof value === "number";
    const isBoolean = typeof value === "boolean";
    const isObject = typeof value === "object" && value !== null;

    if (isEditing) {
      if (isBoolean) {
        return (
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={value}
              onChange={(e) => handleFieldChange(key, e.target.checked)}
              className="rounded"
            />
            <span className="text-sm text-gray-600">{key}</span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleRemoveField(key)}
              className="text-red-600 hover:text-red-700"
            >
              <X className="h-3 w-3" />
            </Button>
          </div>
        );
      } else if (isNumber) {
        return (
          <div className="flex items-center gap-2">
            <Input
              type="number"
              value={value}
              onChange={(e) => handleFieldChange(key, Number(e.target.value))}
              className="flex-1"
            />
            <span className="text-sm text-gray-600">{key}</span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleRemoveField(key)}
              className="text-red-600 hover:text-red-700"
            >
              <X className="h-3 w-3" />
            </Button>
          </div>
        );
      } else if (isString && value.length > 100) {
        return (
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-gray-700">{key}</span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleRemoveField(key)}
                className="text-red-600 hover:text-red-700"
              >
                <X className="h-3 w-3" />
              </Button>
            </div>
            <Textarea
              value={value}
              onChange={(e) => handleFieldChange(key, e.target.value)}
              rows={4}
            />
          </div>
        );
      } else {
        return (
          <div className="flex items-center gap-2">
            <Input
              value={value}
              onChange={(e) => handleFieldChange(key, e.target.value)}
              className="flex-1"
            />
            <span className="text-sm text-gray-600">{key}</span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleRemoveField(key)}
              className="text-red-600 hover:text-red-700"
            >
              <X className="h-3 w-3" />
            </Button>
          </div>
        );
      }
    } else {
      return (
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-gray-700">{key}</span>
            <Badge variant="outline" className="text-xs">
              {typeof value}
            </Badge>
          </div>
          <div className="text-sm text-gray-600">
            {isObject ? (
              <pre className="bg-gray-100 p-2 rounded text-xs overflow-x-auto">
                {JSON.stringify(value, null, 2)}
              </pre>
            ) : (
              <span>{String(value)}</span>
            )}
          </div>
        </div>
      );
    }
  };

  if (!sessionId) {
    return (
      <Card>
        <CardContent className="p-6 text-center text-gray-500">
          <FolderOpen className="h-12 w-12 mx-auto mb-4 text-gray-400" />
          <p>No session selected</p>
          <p className="text-sm">Select a session to view project context</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">Project Context</h3>
          <p className="text-sm text-gray-600">
            Session: {sessionId.slice(0, 8)}...
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={loadContext}
            disabled={isLoading}
          >
            <RefreshCw
              className={`h-4 w-4 mr-2 ${isLoading ? "animate-spin" : ""}`}
            />
            Refresh
          </Button>
          {!isEditing ? (
            <Button
              size="sm"
              onClick={() => setIsEditing(true)}
              disabled={isLoading}
            >
              <Edit3 className="h-4 w-4 mr-2" />
              Edit
            </Button>
          ) : (
            <div className="flex gap-2">
              <Button size="sm" onClick={handleSave} disabled={isLoading}>
                <Save className="h-4 w-4 mr-2" />
                Save
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleCancel}
                disabled={isLoading}
              >
                <X className="h-4 w-4 mr-2" />
                Cancel
              </Button>
            </div>
          )}
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-red-800">
              <Info className="h-4 w-4" />
              <span>{error}</span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Context Content */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Context Data</CardTitle>
            {isEditing && (
              <Button variant="outline" size="sm" onClick={handleAddField}>
                <Plus className="h-4 w-4 mr-2" />
                Add Field
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="text-center py-8">
              <RefreshCw className="h-8 w-8 mx-auto animate-spin text-gray-400" />
              <p className="mt-2 text-gray-600">Loading context...</p>
            </div>
          ) : context ? (
            <div className="space-y-4">
              {Object.keys(editData).length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <FolderOpen className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                  <p>No context data available</p>
                  {isEditing && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleAddField}
                      className="mt-4"
                    >
                      <Plus className="h-4 w-4 mr-2" />
                      Add First Field
                    </Button>
                  )}
                </div>
              ) : (
                <ScrollArea className="h-64">
                  <div className="space-y-4">
                    {Object.entries(editData).map(([key, value]) => (
                      <div key={key} className="p-3 border rounded-lg">
                        {renderField(key, value)}
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              )}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <Info className="h-12 w-12 mx-auto mb-4 text-gray-400" />
              <p>Failed to load context</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Task Summary */}
      {context && context.task_count > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Task Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-4">
              <Badge variant="secondary">{context.task_count} tasks</Badge>
              <p className="text-sm text-gray-600">
                {context.tasks.length} tasks loaded
              </p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
