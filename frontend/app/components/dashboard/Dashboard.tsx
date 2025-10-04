/**
 * Main Dashboard Component
 *
 * Provides the main interface for the puntini system,
 * integrating session management, project context, and task management.
 */

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
// import { Button } from '../ui/button';
import {
  Activity,
  CheckSquare,
  FolderOpen,
  MessageSquare,
  Settings,
  Users,
  Network,
} from "lucide-react";
import { ChatPage } from "../../chat/ChatPage";
import { useSession, type SessionInfo } from "@/utils/session";
import { ProjectContext } from "../project/ProjectContext";
import { SessionManager } from "../session/SessionManager";
import { TaskManager } from "../task/TaskManager";
import { Badge } from "../ui/badge";
// import { Tabs, TabsContent, TabsList, TabsTrigger } from "../ui/tabs";
import { AuthContext } from "../auth/AuthContext";
import { useContext } from "react";
import { GraphContainer } from "../graph/GraphContainer";
import { Status } from "../status/Status";

export const Dashboard: React.FC = () => {
  const { currentSession } = useSession();
  
  // Get auth context with defensive check
  const authContext = useContext(AuthContext);
  const { user } = authContext || { user: null };
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

  // Show loading message if auth context is not available
  if (!authContext) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Loading...</h1>
          <p className="text-gray-600">Initializing authentication...</p>
        </div>
      </div>
    );
  }

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
                  Puntini
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
      <main className="w-full px-4 sm:px-6 lg:px-8 py-8 h-[calc(100vh-80px)] flex flex-col">
        <div className="mb-6 flex-shrink-0">
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
        <div className="flex-1 flex flex-col space-y-6 min-h-0 w-full">
          {/* Tab Navigation */}
          <div className="grid w-full grid-cols-5 bg-gray-100 p-1 rounded-lg">
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
              onClick={() => setActiveTab('graph')}
              className={`flex items-center gap-2 px-4 py-2 rounded-md transition-colors ${
                activeTab === 'graph' ? 'bg-white shadow-sm' : 'hover:bg-gray-50'
              }`}
            >
              <Network className="h-4 w-4" />
              Graph
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
          <div className="flex-1 flex flex-col min-h-0 w-full">
            {/* Chat Tab */}
            <div style={{ display: activeTab === 'chat' ? 'flex' : 'none' }} className="flex-1 flex flex-col min-h-0 w-full">
              <div className="flex-1 flex gap-6 min-h-0 w-full">
                {/* Chat Section - Left Side */}
                <div className="flex-1 flex flex-col min-h-0">
                  <Card className="flex-1 flex flex-col min-h-0">
                    <CardHeader className="flex-shrink-0">
                      <CardTitle>AI Agent Chat</CardTitle>
                    </CardHeader>
                    <CardContent className="flex-1 p-0 min-h-0">
                      <ChatPage />
                    </CardContent>
                  </Card>
                </div>
                
                {/* Status Section - Right Side */}
                <div className="flex-1 flex flex-col min-h-0">
                  <Status sessionId={contextSession?.session_id || null} />
                </div>
              </div>
            </div>

            {/* Sessions Tab */}
            <div style={{ display: activeTab === 'sessions' ? 'flex' : 'none' }} className="flex-1 flex flex-col min-h-0 w-full">
              <SessionManager onSessionSelect={handleSessionSelect} />
            </div>

            {/* Tasks Tab */}
            <div style={{ display: activeTab === 'tasks' ? 'flex' : 'none' }} className="flex-1 flex flex-col min-h-0 w-full">
              <TaskManager sessionId={contextSession?.session_id || "demo-session"} />
            </div>

            {/* Graph Tab */}
            <div style={{ display: activeTab === 'graph' ? 'flex' : 'none' }} className="flex-1 flex flex-col min-h-0 w-full">
              <GraphContainer />
            </div>


            {/* Context Tab */}
            <div style={{ display: activeTab === 'context' ? 'flex' : 'none' }} className="flex-1 flex flex-col min-h-0 w-full">
              <ProjectContext sessionId={contextSession?.session_id || null} />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};
