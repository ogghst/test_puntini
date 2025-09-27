/**
 * Status Message Component
 * 
 * Renders state_update messages as structured markdown highlighting:
 * - Current progress
 * - Planned steps
 * - Confidence
 * - Goal, if present
 */

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
// import { Progress } from "../ui/progress";
import { CheckCircle, Circle, Clock, Target, TrendingUp } from "lucide-react";
import type { StateUpdateData } from "@/utils/session";

interface StatusMessageProps {
  data: StateUpdateData;
  timestamp: string;
}

/**
 * StatusMessage component for rendering structured status updates
 * 
 * @param props - Component props including state update data and timestamp
 * @returns JSX element representing a structured status message
 */
export const StatusMessage: React.FC<StatusMessageProps> = ({ data, timestamp }) => {
  const { 
    update_type, 
    current_step, 
    todo_list = [], 
    entities_created = [], 
    progress = [], 
    failures = [] 
  } = data;

  // Calculate overall progress percentage
  const completedSteps = todo_list.filter(todo => todo.status === "done").length;
  const totalSteps = todo_list.length;
  const progressPercentage = totalSteps > 0 ? (completedSteps / totalSteps) * 100 : 0;

  // Get confidence from entities (if available)
  const avgConfidence = entities_created.length > 0 
    ? entities_created.reduce((sum, entity) => sum + entity.confidence, 0) / entities_created.length
    : 0;

  return (
    <Card className="w-full bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-semibold text-blue-900 flex items-center gap-2">
            <Target className="h-5 w-5" />
            Agent Status Update
          </CardTitle>
          <Badge variant="outline" className="text-xs">
            {new Date(timestamp).toLocaleTimeString()}
          </Badge>
        </div>
        <div className="flex items-center gap-2 text-sm text-blue-700">
          <span className="font-medium">Type:</span>
          <Badge variant="secondary" className="text-xs">
            {update_type}
          </Badge>
          <span className="font-medium ml-2">Step:</span>
          <Badge variant="outline" className="text-xs">
            {current_step}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Overall Progress */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="font-medium text-gray-700">Overall Progress</span>
            <span className="text-gray-600">{completedSteps}/{totalSteps} steps</span>
          </div>
          <div className="relative h-2 w-full overflow-hidden rounded-full bg-gray-200">
            <div
              className="h-full bg-blue-600 transition-all duration-300 ease-in-out"
              style={{ width: `${progressPercentage}%` }}
            />
          </div>
          <div className="text-xs text-gray-500">
            {progressPercentage.toFixed(0)}% complete
          </div>
        </div>

        {/* Planned Steps */}
        {todo_list.length > 0 && (
          <div className="space-y-2">
            <h4 className="font-medium text-gray-700 flex items-center gap-2">
              <Clock className="h-4 w-4" />
              Planned Steps
            </h4>
            <div className="space-y-2">
              {todo_list.map((todo, index) => (
                <div 
                  key={index}
                  className={`flex items-start gap-3 p-3 rounded-lg border ${
                    todo.status === "done" 
                      ? "bg-green-50 border-green-200" 
                      : "bg-gray-50 border-gray-200"
                  }`}
                >
                  <div className="flex-shrink-0 mt-0.5">
                    {todo.status === "done" ? (
                      <CheckCircle className="h-4 w-4 text-green-600" />
                    ) : (
                      <Circle className="h-4 w-4 text-gray-400" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-medium text-gray-900">
                        Step {todo.step_number || index + 1}
                      </span>
                      {todo.tool_name && (
                        <Badge variant="outline" className="text-xs">
                          {todo.tool_name}
                        </Badge>
                      )}
                      {todo.estimated_complexity && (
                        <Badge 
                          variant="outline" 
                          className={`text-xs ${
                            todo.estimated_complexity === "high" ? "border-red-300 text-red-700" :
                            todo.estimated_complexity === "medium" ? "border-yellow-300 text-yellow-700" :
                            "border-green-300 text-green-700"
                          }`}
                        >
                          {todo.estimated_complexity}
                        </Badge>
                      )}
                    </div>
                    <p className="text-sm text-gray-600">{todo.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Entities Created */}
        {entities_created.length > 0 && (
          <div className="space-y-2">
            <h4 className="font-medium text-gray-700 flex items-center gap-2">
              <TrendingUp className="h-4 w-4" />
              Entities Created
            </h4>
            <div className="grid gap-2">
              {entities_created.map((entity, index) => (
                <div key={index} className="p-3 bg-white rounded-lg border border-gray-200">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Badge variant="secondary" className="text-xs">
                        {entity.type}
                      </Badge>
                      <span className="font-medium text-gray-900">{entity.name}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-gray-500">Confidence:</span>
                      <Badge 
                        variant="outline" 
                        className={`text-xs ${
                          entity.confidence >= 0.8 ? "border-green-300 text-green-700" :
                          entity.confidence >= 0.6 ? "border-yellow-300 text-yellow-700" :
                          "border-red-300 text-red-700"
                        }`}
                      >
                        {(entity.confidence * 100).toFixed(0)}%
                      </Badge>
                    </div>
                  </div>
                  <div className="text-sm text-gray-600">
                    <span className="font-medium">Label:</span> {entity.label}
                  </div>
                  {Object.keys(entity.properties).length > 0 && (
                    <div className="text-sm text-gray-600 mt-1">
                      <span className="font-medium">Properties:</span>
                      <div className="mt-1 pl-2 border-l-2 border-gray-200">
                        {Object.entries(entity.properties).map(([key, value]) => (
                          <div key={key} className="text-xs">
                            <span className="font-medium">{key}:</span> {String(value)}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
            {avgConfidence > 0 && (
              <div className="text-xs text-gray-500 text-center">
                Average Confidence: {(avgConfidence * 100).toFixed(0)}%
              </div>
            )}
          </div>
        )}

        {/* Progress Log */}
        {progress.length > 0 && (
          <div className="space-y-2">
            <h4 className="font-medium text-gray-700">Progress Log</h4>
            <div className="space-y-1">
              {progress.map((logEntry, index) => (
                <div key={index} className="text-sm text-gray-600 p-2 bg-white rounded border-l-4 border-blue-300">
                  {logEntry}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Failures */}
        {failures.length > 0 && (
          <div className="space-y-2">
            <h4 className="font-medium text-red-700">Failures</h4>
            <div className="space-y-1">
              {failures.map((failure, index) => (
                <div key={index} className="text-sm text-red-600 p-2 bg-red-50 rounded border-l-4 border-red-300">
                  {typeof failure === 'string' ? failure : JSON.stringify(failure)}
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
