/**
 * Status Message Component
 * 
 * Renders state_update messages showing only current step and progress.
 */

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { Clock, Target } from "lucide-react";
import type { StateUpdateData } from "@/utils/session";

interface StatusMessageProps {
  data: StateUpdateData;
  timestamp: string;
}

/**
 * StatusMessage component for rendering simplified status updates
 * 
 * @param props - Component props including state update data and timestamp
 * @returns JSX element representing a simplified status message
 */
export const StatusMessage: React.FC<StatusMessageProps> = ({ data, timestamp }) => {
  const { 
    update_type, 
    current_step, 
    todo_list = [], 
    progress = [] 
  } = data;

  // Calculate overall progress percentage
  const completedSteps = todo_list.filter(todo => todo.status === "done").length;
  const totalSteps = todo_list.length;
  const progressPercentage = totalSteps > 0 ? (completedSteps / totalSteps) * 100 : 0;

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

      </CardHeader>

      <CardContent className="space-y-4">
        {/* Current Step */}
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-blue-600" />
            <span className="font-medium text-gray-700">Current Step:</span>
            <Badge variant="outline" className="text-sm">
              {current_step}
            </Badge>
          </div>

        </div>

        {/* Progress Summary */}
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Target className="h-4 w-4 text-green-600" />
            <span className="font-medium text-gray-700">Progress:</span>
            <span className="text-sm text-gray-600">
              {completedSteps} of {totalSteps} steps completed ({progressPercentage.toFixed(0)}%)
            </span>
          </div>
        </div>

        {/* Latest Progress Entry */}
        {progress.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Target className="h-4 w-4 text-blue-600" />
              <span className="font-medium text-gray-700">Latest Update:</span>
            </div>
            <div className="text-sm text-gray-600 pl-6 bg-blue-50 p-3 rounded-lg border-l-4 border-blue-300">
              {progress[progress.length - 1]}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
