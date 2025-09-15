/**
 * Session Manager Component
 *
 * Provides a comprehensive session management interface for the business
 * improvement project management system.
 */

import {
  Activity,
  AlertCircle,
  Clock,
  Eye,
  Plus,
  RefreshCw,
  Trash2,
  Users,
} from "lucide-react";
import React, { useEffect, useState } from "react";
import {
  SessionAPI,
  SessionAPIError,
  useSession,
  type SessionInfo,
  type SessionStats,
} from "../../utils/session";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { ScrollArea } from "../ui/scroll-area";

interface SessionManagerProps {
  onSessionSelect?: (session: SessionInfo) => void;
  selectedSessionId?: string;
}

export const SessionManager: React.FC<SessionManagerProps> = ({
  onSessionSelect,
  selectedSessionId,
}) => {
  const { currentSession, refreshSession } = useSession();
  const [sessions, setSessions] = useState<SessionInfo[]>([]);
  const [stats, setStats] = useState<SessionStats | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load sessions and stats
  const loadData = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const [sessionsData, statsData] = await Promise.all([
        SessionAPI.listSessions(),
        SessionAPI.getSessionStats(),
      ]);

      setSessions(sessionsData.sessions);
      setStats(statsData);
    } catch (err) {
      const apiError =
        err instanceof SessionAPIError
          ? err
          : new SessionAPIError("Failed to load data");
      setError(apiError.message);
    } finally {
      setIsLoading(false);
    }
  };

  // Load data on component mount
  useEffect(() => {
    loadData();
  }, []);

  // Refresh current session
  const handleRefreshSession = async () => {
    if (currentSession) {
      try {
        await refreshSession();
        await loadData(); // Reload all data
      } catch {
        // console.error('Failed to refresh session:', err);
      }
    }
  };

  // Create new session
  const handleCreateSession = async () => {
    try {
      const newSession = await SessionAPI.createSession({
        user_id: "frontend_user",
        metadata: { source: "session_manager" },
      });

      await loadData(); // Reload sessions

      if (onSessionSelect) {
        onSessionSelect(newSession);
      }
    } catch (err) {
      const apiError =
        err instanceof SessionAPIError
          ? err
          : new SessionAPIError("Failed to create session");
      setError(apiError.message);
    }
  };

  // Destroy session
  const handleDestroySession = async (sessionId: string) => {
    try {
      await SessionAPI.destroySession(sessionId);
      await loadData(); // Reload sessions
    } catch (err) {
      const apiError =
        err instanceof SessionAPIError
          ? err
          : new SessionAPIError("Failed to destroy session");
      setError(apiError.message);
    }
  };

  // Get status badge color
  const getStatusBadgeColor = (status: string) => {
    switch (status) {
      case "active":
        return "bg-green-100 text-green-800";
      case "initializing":
        return "bg-blue-100 text-blue-800";
      case "paused":
        return "bg-yellow-100 text-yellow-800";
      case "expired":
        return "bg-gray-100 text-gray-800";
      case "error":
        return "bg-red-100 text-red-800";
      case "cleaning_up":
        return "bg-orange-100 text-orange-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  // Format duration
  const formatDuration = (createdAt: string, lastActivity: string) => {
    const created = new Date(createdAt);
    const last = new Date(lastActivity);
    const diffMs = last.getTime() - created.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));

    if (diffMins < 1) return "< 1m";
    if (diffMins < 60) return `${diffMins}m`;

    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h`;

    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d`;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Session Manager</h2>
          <p className="text-gray-600">
            Manage user sessions and monitor activity
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={loadData}
            disabled={isLoading}
          >
            <RefreshCw
              className={`h-4 w-4 mr-2 ${isLoading ? "animate-spin" : ""}`}
            />
            Refresh
          </Button>
          <Button size="sm" onClick={handleCreateSession} disabled={isLoading}>
            <Plus className="h-4 w-4 mr-2" />
            New Session
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

      {/* Statistics */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <Users className="h-5 w-5 text-blue-600" />
                <div>
                  <p className="text-sm text-gray-600">Total Sessions</p>
                  <p className="text-2xl font-bold">{stats.total_sessions}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <Activity className="h-5 w-5 text-green-600" />
                <div>
                  <p className="text-sm text-gray-600">Active Sessions</p>
                  <p className="text-2xl font-bold">{stats.active_sessions}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <Clock className="h-5 w-5 text-gray-600" />
                <div>
                  <p className="text-sm text-gray-600">Expired Sessions</p>
                  <p className="text-2xl font-bold">{stats.expired_sessions}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <AlertCircle className="h-5 w-5 text-red-600" />
                <div>
                  <p className="text-sm text-gray-600">Error Sessions</p>
                  <p className="text-2xl font-bold">{stats.error_sessions}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Current Session Info */}
      {currentSession && (
        <Card className="border-blue-200 bg-blue-50">
          <CardHeader>
            <CardTitle className="text-lg">Current Session</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">
                  Session {currentSession.session_id.slice(0, 8)}...
                </p>
                <p className="text-sm text-gray-600">
                  Created:{" "}
                  {new Date(currentSession.created_at).toLocaleString()}
                </p>
                <p className="text-sm text-gray-600">
                  Agents: {currentSession.agent_count} | Tasks:{" "}
                  {currentSession.task_count}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <Badge className={getStatusBadgeColor(currentSession.status)}>
                  {currentSession.status}
                </Badge>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleRefreshSession}
                >
                  <RefreshCw className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Sessions List */}
      <Card>
        <CardHeader>
          <CardTitle>All Sessions</CardTitle>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-96">
            <div className="space-y-2">
              {sessions.map((session) => (
                <button
                  key={session.session_id}
                  className={`w-full text-left p-4 border rounded-lg cursor-pointer transition-colors ${
                    selectedSessionId === session.session_id
                      ? "border-blue-500 bg-blue-50"
                      : "border-gray-200 hover:border-gray-300"
                  }`}
                  onClick={() => onSessionSelect?.(session)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <p className="font-medium">
                          {session.user_id} - {session.session_id.slice(0, 8)}
                          ...
                        </p>
                        <Badge className={getStatusBadgeColor(session.status)}>
                          {session.status}
                        </Badge>
                        {session.is_active && (
                          <Badge className="bg-green-100 text-green-800">
                            Active
                          </Badge>
                        )}
                      </div>

                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-gray-600">
                        <div>
                          <p className="font-medium">Created</p>
                          <p>{new Date(session.created_at).toLocaleString()}</p>
                        </div>
                        <div>
                          <p className="font-medium">Last Activity</p>
                          <p>
                            {new Date(session.last_activity).toLocaleString()}
                          </p>
                        </div>
                        <div>
                          <p className="font-medium">Duration</p>
                          <p>
                            {formatDuration(
                              session.created_at,
                              session.last_activity
                            )}
                          </p>
                        </div>
                        <div>
                          <p className="font-medium">Resources</p>
                          <p>
                            {session.agent_count} agents, {session.task_count}{" "}
                            tasks
                          </p>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 ml-4">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          onSessionSelect?.(session);
                        }}
                      >
                        <Eye className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDestroySession(session.session_id);
                        }}
                        className="text-red-600 hover:text-red-700"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </button>
              ))}

              {sessions.length === 0 && !isLoading && (
                <div className="text-center py-8 text-gray-500">
                  No sessions found
                </div>
              )}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
};
