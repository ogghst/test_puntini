/**
 * Task Manager Component
 *
 * Manages tasks within a session, providing interface for creating, viewing,
 * and managing project tasks.
 */

import {
  AlertCircle,
  CheckCircle,
  CheckSquare,
  Circle,
  Clock,
  Edit3,
  // Trash2,
  Filter,
  Plus,
  RefreshCw,
  Save,
  X,
} from "lucide-react";
import React, { useCallback, useEffect, useState } from "react";
import {
  SessionAPI,
  SessionAPIError,
  type TaskInfo,
} from "../../utils/session";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Input } from "../ui/input";
import { ScrollArea } from "../ui/scroll-area";
import { Textarea } from "../ui/textarea";

interface TaskManagerProps {
  sessionId: string | null;
  onTaskUpdate?: (tasks: TaskInfo[]) => void;
}

type TaskStatus = "pending" | "in_progress" | "completed" | "cancelled";
type TaskPriority = "low" | "medium" | "high" | "urgent";

export const TaskManager: React.FC<TaskManagerProps> = ({
  sessionId,
  onTaskUpdate,
}) => {
  const [tasks, setTasks] = useState<TaskInfo[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  // const [editingTask, setEditingTask] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<{
    status?: TaskStatus;
    priority?: TaskPriority;
  }>({});

  const [newTask, setNewTask] = useState<Partial<TaskInfo>>({
    title: "",
    description: "",
    status: "pending",
    priority: "medium",
  });

  // Load tasks
  const loadTasks = useCallback(async () => {
    if (!sessionId) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await SessionAPI.getTasks(sessionId);
      setTasks(response.tasks);

      if (onTaskUpdate) {
        onTaskUpdate(response.tasks);
      }
    } catch (err) {
      const apiError =
        err instanceof SessionAPIError
          ? err
          : new SessionAPIError("Failed to load tasks");
      setError(apiError.message);
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, onTaskUpdate]);

  // Load tasks on session change
  useEffect(() => {
    loadTasks();
  }, [sessionId, loadTasks]);

  // Create new task
  const handleCreateTask = async () => {
    if (!sessionId || !newTask.title?.trim()) return;

    setIsLoading(true);
    setError(null);

    try {
      await SessionAPI.addTask(sessionId, {
        title: newTask.title,
        description: newTask.description || "",
        status: newTask.status || "pending",
        priority: newTask.priority || "medium",
        metadata: {},
      });

      await loadTasks(); // Reload tasks
      setNewTask({
        title: "",
        description: "",
        status: "pending",
        priority: "medium",
      });
      setIsCreating(false);
    } catch (err) {
      const apiError =
        err instanceof SessionAPIError
          ? err
          : new SessionAPIError("Failed to create task");
      setError(apiError.message);
    } finally {
      setIsLoading(false);
    }
  };

  // Cancel creating task
  const handleCancelCreate = () => {
    setNewTask({
      title: "",
      description: "",
      status: "pending",
      priority: "medium",
    });
    setIsCreating(false);
  };

  // Start editing task
  const handleStartEdit = (task: TaskInfo) => {
    setEditingTask(task.id);
  };

  // Cancel editing
  // const handleCancelEdit = () => {
  //   setEditingTask(null);
  // };

  // Get status badge color
  const getStatusBadgeColor = (status: TaskStatus) => {
    switch (status) {
      case "pending":
        return "bg-gray-100 text-gray-800";
      case "in_progress":
        return "bg-blue-100 text-blue-800";
      case "completed":
        return "bg-green-100 text-green-800";
      case "cancelled":
        return "bg-red-100 text-red-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  // Get priority badge color
  const getPriorityBadgeColor = (priority: TaskPriority) => {
    switch (priority) {
      case "low":
        return "bg-green-100 text-green-800";
      case "medium":
        return "bg-yellow-100 text-yellow-800";
      case "high":
        return "bg-orange-100 text-orange-800";
      case "urgent":
        return "bg-red-100 text-red-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  // Get status icon
  const getStatusIcon = (status: TaskStatus) => {
    switch (status) {
      case "pending":
        return <Circle className="h-4 w-4" />;
      case "in_progress":
        return <Clock className="h-4 w-4" />;
      case "completed":
        return <CheckCircle className="h-4 w-4" />;
      case "cancelled":
        return <X className="h-4 w-4" />;
      default:
        return <Circle className="h-4 w-4" />;
    }
  };

  // Filter tasks
  const filteredTasks = tasks.filter((task) => {
    if (filter.status && task.status !== filter.status) return false;
    if (filter.priority && task.priority !== filter.priority) return false;
    return true;
  });

  // Get task counts by status
  const taskCounts = {
    total: tasks.length,
    pending: tasks.filter((t) => t.status === "pending").length,
    in_progress: tasks.filter((t) => t.status === "in_progress").length,
    completed: tasks.filter((t) => t.status === "completed").length,
    cancelled: tasks.filter((t) => t.status === "cancelled").length,
  };

  if (!sessionId) {
    return (
      <Card>
        <CardContent className="p-6 text-center text-gray-500">
          <CheckSquare className="h-12 w-12 mx-auto mb-4 text-gray-400" />
          <p>No session selected</p>
          <p className="text-sm">Select a session to view tasks</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">Task Manager</h3>
          <p className="text-sm text-gray-600">
            Session: {sessionId.slice(0, 8)}...
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={loadTasks}
            disabled={isLoading}
          >
            <RefreshCw
              className={`h-4 w-4 mr-2 ${isLoading ? "animate-spin" : ""}`}
            />
            Refresh
          </Button>
          <Button
            size="sm"
            onClick={() => setIsCreating(true)}
            disabled={isLoading || isCreating}
          >
            <Plus className="h-4 w-4 mr-2" />
            New Task
          </Button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-red-800">
              <AlertCircle className="h-4 w-4" />
              <span>{error}</span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Task Statistics */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <CheckSquare className="h-5 w-5 text-blue-600" />
              <div>
                <p className="text-sm text-gray-600">Total</p>
                <p className="text-2xl font-bold">{taskCounts.total}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Circle className="h-5 w-5 text-gray-600" />
              <div>
                <p className="text-sm text-gray-600">Pending</p>
                <p className="text-2xl font-bold">{taskCounts.pending}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Clock className="h-5 w-5 text-blue-600" />
              <div>
                <p className="text-sm text-gray-600">In Progress</p>
                <p className="text-2xl font-bold">{taskCounts.in_progress}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-green-600" />
              <div>
                <p className="text-sm text-gray-600">Completed</p>
                <p className="text-2xl font-bold">{taskCounts.completed}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <X className="h-5 w-5 text-red-600" />
              <div>
                <p className="text-sm text-gray-600">Cancelled</p>
                <p className="text-2xl font-bold">{taskCounts.cancelled}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Filters
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            <div>
              <label
                htmlFor="status-filter"
                className="text-sm font-medium text-gray-700"
              >
                Status
              </label>
              <select
                id="status-filter"
                value={filter.status || ""}
                onChange={(e) =>
                  setFilter((prev) => ({
                    ...prev,
                    status: (e.target.value as TaskStatus) || undefined,
                  }))
                }
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              >
                <option value="">All Statuses</option>
                <option value="pending">Pending</option>
                <option value="in_progress">In Progress</option>
                <option value="completed">Completed</option>
                <option value="cancelled">Cancelled</option>
              </select>
            </div>

            <div>
              <label
                htmlFor="priority-filter"
                className="text-sm font-medium text-gray-700"
              >
                Priority
              </label>
              <select
                id="priority-filter"
                value={filter.priority || ""}
                onChange={(e) =>
                  setFilter((prev) => ({
                    ...prev,
                    priority: (e.target.value as TaskPriority) || undefined,
                  }))
                }
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              >
                <option value="">All Priorities</option>
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="urgent">Urgent</option>
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Create Task Form */}
      {isCreating && (
        <Card className="border-blue-200 bg-blue-50">
          <CardHeader>
            <CardTitle>Create New Task</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label
                htmlFor="task-title"
                className="text-sm font-medium text-gray-700"
              >
                Title
              </label>
              <Input
                id="task-title"
                value={newTask.title || ""}
                onChange={(e) =>
                  setNewTask((prev) => ({ ...prev, title: e.target.value }))
                }
                placeholder="Enter task title"
                className="mt-1"
              />
            </div>

            <div>
              <label
                htmlFor="task-description"
                className="text-sm font-medium text-gray-700"
              >
                Description
              </label>
              <Textarea
                id="task-description"
                value={newTask.description || ""}
                onChange={(e) =>
                  setNewTask((prev) => ({
                    ...prev,
                    description: e.target.value,
                  }))
                }
                placeholder="Enter task description"
                rows={3}
                className="mt-1"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label
                  htmlFor="new-task-status"
                  className="text-sm font-medium text-gray-700"
                >
                  Status
                </label>
                <select
                  id="new-task-status"
                  value={newTask.status || "pending"}
                  onChange={(e) =>
                    setNewTask((prev) => ({
                      ...prev,
                      status: e.target.value as TaskStatus,
                    }))
                  }
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                >
                  <option value="pending">Pending</option>
                  <option value="in_progress">In Progress</option>
                  <option value="completed">Completed</option>
                  <option value="cancelled">Cancelled</option>
                </select>
              </div>

              <div>
                <label
                  htmlFor="new-task-priority"
                  className="text-sm font-medium text-gray-700"
                >
                  Priority
                </label>
                <select
                  id="new-task-priority"
                  value={newTask.priority || "medium"}
                  onChange={(e) =>
                    setNewTask((prev) => ({
                      ...prev,
                      priority: e.target.value as TaskPriority,
                    }))
                  }
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="urgent">Urgent</option>
                </select>
              </div>
            </div>

            <div className="flex gap-2">
              <Button
                onClick={handleCreateTask}
                disabled={isLoading || !newTask.title?.trim()}
              >
                <Save className="h-4 w-4 mr-2" />
                Create Task
              </Button>
              <Button
                variant="outline"
                onClick={handleCancelCreate}
                disabled={isLoading}
              >
                <X className="h-4 w-4 mr-2" />
                Cancel
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tasks List */}
      <Card>
        <CardHeader>
          <CardTitle>Tasks ({filteredTasks.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="text-center py-8">
              <RefreshCw className="h-8 w-8 mx-auto animate-spin text-gray-400" />
              <p className="mt-2 text-gray-600">Loading tasks...</p>
            </div>
          ) : filteredTasks.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <CheckSquare className="h-12 w-12 mx-auto mb-4 text-gray-400" />
              <p>No tasks found</p>
              {Object.keys(filter).length > 0 && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setFilter({})}
                  className="mt-4"
                >
                  Clear Filters
                </Button>
              )}
            </div>
          ) : (
            <ScrollArea className="h-96">
              <div className="space-y-2">
                {filteredTasks.map((task) => (
                  <div
                    key={task.id}
                    className="p-4 border rounded-lg hover:border-gray-300 transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          {getStatusIcon(task.status)}
                          <h4 className="font-medium">{task.title}</h4>
                          <Badge className={getStatusBadgeColor(task.status)}>
                            {task.status}
                          </Badge>
                          <Badge
                            className={getPriorityBadgeColor(task.priority)}
                          >
                            {task.priority}
                          </Badge>
                        </div>

                        {task.description && (
                          <p className="text-sm text-gray-600 mb-2">
                            {task.description}
                          </p>
                        )}

                        <div className="flex items-center gap-4 text-xs text-gray-500">
                          <span>ID: {task.id}</span>
                          <span>
                            Created:{" "}
                            {new Date(task.created_at).toLocaleString()}
                          </span>
                        </div>
                      </div>

                      <div className="flex items-center gap-2 ml-4">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleStartEdit(task)}
                        >
                          <Edit3 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
