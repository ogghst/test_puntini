/**
 * Main Dashboard Component
 *
 * Provides the main interface for the business improvement project management system,
 * integrating session management, project context, and task management.
 */

import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
// import { Button } from '../ui/button';
import {
  Activity,
  CheckSquare,
  FolderOpen,
  MessageSquare,
  Settings,
  Users,
} from "lucide-react";
import { ChatPage } from "../../chat/ChatPage";
import { useSession, type SessionInfo } from "../../utils/session";
import { ProjectContext } from "../project/ProjectContext";
import { SessionManager } from "../session/SessionManager";
import { TaskManager } from "../task/TaskManager";
import { Badge } from "../ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../ui/tabs";

export const Dashboard: React.FC = () => {
  const { currentSession } = useSession();
  const [selectedSession, setSelectedSession] = useState<SessionInfo | null>(
    null
  );
  const [activeTab, setActiveTab] = useState("chat");

  // Handle session selection
  const handleSessionSelect = (session: SessionInfo) => {
    setSelectedSession(session);
    setActiveTab("chat"); // Switch to chat when selecting a session
  };

  // Get current session for context
  const contextSession = selectedSession || currentSession;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <Activity className="h-8 w-8 text-blue-600" />
                <h1 className="text-xl font-bold text-gray-900">
                  Business Improvement Project Management
                </h1>
              </div>
              {currentSession && (
                <Badge variant="secondary" className="ml-4">
                  Session: {currentSession.session_id.slice(0, 8)}...
                </Badge>
              )}
            </div>

            <div className="flex items-center gap-4">
              {currentSession && (
                <div className="text-sm text-gray-600">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span>Active</span>
                  </div>
                  <div className="text-xs text-gray-500">
                    {currentSession.agent_count} agents,{" "}
                    {currentSession.task_count} tasks
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Tabs
          value={activeTab}
          onValueChange={setActiveTab}
          className="space-y-6"
        >
          {/* Navigation Tabs */}
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="chat" className="flex items-center gap-2">
              <MessageSquare className="h-4 w-4" />
              Chat
            </TabsTrigger>
            <TabsTrigger value="sessions" className="flex items-center gap-2">
              <Users className="h-4 w-4" />
              Sessions
            </TabsTrigger>
            <TabsTrigger value="context" className="flex items-center gap-2">
              <FolderOpen className="h-4 w-4" />
              Project Context
            </TabsTrigger>
            <TabsTrigger value="tasks" className="flex items-center gap-2">
              <CheckSquare className="h-4 w-4" />
              Tasks
            </TabsTrigger>
            <TabsTrigger value="settings" className="flex items-center gap-2">
              <Settings className="h-4 w-4" />
              Settings
            </TabsTrigger>
          </TabsList>

          {/* Chat Tab */}
          <TabsContent value="chat" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MessageSquare className="h-5 w-5" />
                  Agent Chat
                </CardTitle>
                <p className="text-sm text-gray-600">
                  Interact with AI agents to manage your business improvement
                  projects
                </p>
              </CardHeader>
              <CardContent className="p-0">
                <div className="h-[600px]">
                  <ChatPage />
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Sessions Tab */}
          <TabsContent value="sessions" className="space-y-6">
            <SessionManager
              onSessionSelect={handleSessionSelect}
              selectedSessionId={selectedSession?.session_id}
            />
          </TabsContent>

          {/* Project Context Tab */}
          <TabsContent value="context" className="space-y-6">
            <ProjectContext
              sessionId={contextSession?.session_id || null}
              onContextUpdate={(_context) => {
                // console.log('Context updated:', context);
              }}
            />
          </TabsContent>

          {/* Tasks Tab */}
          <TabsContent value="tasks" className="space-y-6">
            <TaskManager
              sessionId={contextSession?.session_id || null}
              onTaskUpdate={(_tasks) => {
                // console.log('Tasks updated:', tasks);
              }}
            />
          </TabsContent>

          {/* Settings Tab */}
          <TabsContent value="settings" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Settings className="h-5 w-5" />
                  Settings
                </CardTitle>
                <p className="text-sm text-gray-600">
                  Configure your application settings
                </p>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* API Configuration */}
                  <div className="space-y-4">
                    <h3 className="text-lg font-medium">API Configuration</h3>
                    <div className="space-y-2">
                      <label
                        htmlFor="backend-url"
                        className="text-sm font-medium text-gray-700"
                      >
                        Backend URL
                      </label>
                      <input
                        id="backend-url"
                        type="text"
                        value="http://localhost:8001"
                        disabled
                        className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-gray-500"
                      />
                      <p className="text-xs text-gray-500">
                        Backend API endpoint (read-only)
                      </p>
                    </div>
                  </div>

                  {/* Session Configuration */}
                  <div className="space-y-4">
                    <h3 className="text-lg font-medium">
                      Session Configuration
                    </h3>
                    <div className="space-y-2">
                      <label
                        htmlFor="current-session"
                        className="text-sm font-medium text-gray-700"
                      >
                        Current Session
                      </label>
                      <div className="p-3 bg-gray-50 rounded-md">
                        {currentSession ? (
                          <div className="space-y-1">
                            <p className="text-sm font-medium">
                              {currentSession.session_id}
                            </p>
                            <p className="text-xs text-gray-600">
                              Status: {currentSession.status} | Created:{" "}
                              {new Date(
                                currentSession.created_at
                              ).toLocaleString()}
                            </p>
                          </div>
                        ) : (
                          <p className="text-sm text-gray-500">
                            No active session
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Application Info */}
                <div className="pt-4 border-t border-gray-200">
                  <h3 className="text-lg font-medium mb-4">
                    Application Information
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                    <div>
                      <p className="font-medium text-gray-700">Version</p>
                      <p className="text-gray-600">0.1.0</p>
                    </div>
                    <div>
                      <p className="font-medium text-gray-700">Environment</p>
                      <p className="text-gray-600">Development</p>
                    </div>
                    <div>
                      <p className="font-medium text-gray-700">Last Updated</p>
                      <p className="text-gray-600">
                        {new Date().toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
};
