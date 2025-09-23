/**
 * Main Dashboard Component
 *
 * Provides the main interface for the business improvement project management system,
 * integrating session management, project context, and task management.
 */

import { useState, useEffect } from "react";
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
import { useSession, type SessionInfo } from "@/utils/session";
import { ProjectContext } from "../project/ProjectContext";
import { SessionManager } from "../session/SessionManager";
import { TaskManager } from "../task/TaskManager";
import { Badge } from "../ui/badge";
// import { Tabs, TabsContent, TabsList, TabsTrigger } from "../ui/tabs";
import { useAuth } from "../auth/AuthContext";

export const Dashboard: React.FC = () => {
  const { currentSession, createSession } = useSession();
  const { user } = useAuth();
  const [selectedSession, setSelectedSession] = useState<SessionInfo | null>(
    null
  );
  const [activeTab, setActiveTab] = useState("chat");

  // Auto-create a session when Dashboard loads
  useEffect(() => {
    if (!currentSession) {
      createSession({ user_id: "demo-user" }).catch(() => {
        // Failed to create session
      });
    }
  }, [currentSession, createSession]);

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
              {user && (
                <Badge variant="secondary">
                  Welcome, {user.full_name || user.username}
                </Badge>
              )}
            </div>
            <nav className="flex items-center space-x-4">
              <button
                className="text-sm font-medium text-gray-700 hover:text-gray-900"
              >
                <Settings className="h-5 w-5" />
              </button>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-gray-900">Dashboard</h2>
          <p className="text-gray-600">
            Manage your business improvement projects and interact with AI agents.
          </p>
          {contextSession && (
            <p className="text-xs text-gray-500 mt-1">
              Session ID: {contextSession.session_id}
            </p>
          )}
        </div>

        {/* Custom Tab Implementation */}
        <div className="space-y-6">
          {/* Tab Navigation */}
          <div className="grid w-full grid-cols-4 bg-gray-100 p-1 rounded-lg">
            <button 
              onClick={() => setActiveTab('chat')}
              className={`flex items-center gap-2 px-4 py-2 rounded-md transition-colors ${
                activeTab === 'chat' ? 'bg-white shadow-sm' : 'hover:bg-gray-50'
              }`}
            >
              <MessageSquare className="h-4 w-4" />
              Chat
            </button>
            <button 
              onClick={() => setActiveTab('sessions')}
              className={`flex items-center gap-2 px-4 py-2 rounded-md transition-colors ${
                activeTab === 'sessions' ? 'bg-white shadow-sm' : 'hover:bg-gray-50'
              }`}
            >
              <Users className="h-4 w-4" />
              Sessions
            </button>
            <button 
              onClick={() => setActiveTab('tasks')}
              className={`flex items-center gap-2 px-4 py-2 rounded-md transition-colors ${
                activeTab === 'tasks' ? 'bg-white shadow-sm' : 'hover:bg-gray-50'
              }`}
            >
              <CheckSquare className="h-4 w-4" />
              Tasks
            </button>
            <button 
              className="flex items-center gap-2 px-4 py-2 rounded-md opacity-50 cursor-not-allowed" 
              disabled
            >
              <FolderOpen className="h-4 w-4" />
              Context
            </button>
          </div>

          {/* Tab Content */}
          <div className="mt-6">
            {/* Chat Tab */}
            <div style={{ display: activeTab === 'chat' ? 'block' : 'none' }}>
              <Card>
                <CardHeader>
                  <CardTitle>AI Agent Chat</CardTitle>
                </CardHeader>
                <CardContent className="p-0">
                  <ChatPage />
                </CardContent>
              </Card>
            </div>

            {/* Sessions Tab */}
            <div style={{ display: activeTab === 'sessions' ? 'block' : 'none' }}>
              <SessionManager onSessionSelect={handleSessionSelect} />
            </div>

            {/* Tasks Tab */}
            <div style={{ display: activeTab === 'tasks' ? 'block' : 'none' }}>
              <TaskManager sessionId={contextSession?.session_id || "demo-session"} />
            </div>

            {/* Context Tab */}
            <div style={{ display: activeTab === 'context' ? 'block' : 'none' }}>
              <ProjectContext sessionId={contextSession?.session_id || null} />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};
