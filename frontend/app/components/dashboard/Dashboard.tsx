/**
 * Main Dashboard Component
 *
 * Provides the main interface for the business improvement project management system,
 * integrating session management, project context, and task management.
 */

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Button } from '../ui/button';
import {
  Activity,
  CheckSquare,
  FolderOpen,
  MessageSquare,
  Settings,
  Users,
  GitMerge,
} from "lucide-react";
import { ChatPage } from "../../chat/ChatPage";
import GraphPage from "../../routes/graph";
import { useSession, type SessionInfo } from "@/utils/session";
import { ProjectContext } from "../project/ProjectContext";
import { SessionManager } from "../session/SessionManager";
import { TaskManager } from "../task/TaskManager";
import { Badge } from "../ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../ui/tabs";
import { useAuth } from "../auth/AuthContext";

export const Dashboard: React.FC = () => {
  const { currentSession } = useSession();
  const { user } = useAuth();
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
              {user && (
                <Badge variant="secondary">
                  Welcome, {user.full_name || user.username}
                </Badge>
              )}
            </div>
            <nav className="flex items-center space-x-4">
              <Button variant="ghost" size="icon">
                <Settings className="h-5 w-5" />
              </Button>
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
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="chat" className="flex items-center gap-2">
              <MessageSquare className="h-4 w-4" />
              Chat
            </TabsTrigger>
            <TabsTrigger value="graph" className="flex items-center gap-2">
              <GitMerge className="h-4 w-4" />
              Graph
            </TabsTrigger>
            <TabsTrigger value="sessions" className="flex items-center gap-2">
              <Users className="h-4 w-4" />
              Sessions
            </TabsTrigger>
            <TabsTrigger value="tasks" className="flex items-center gap-2">
              <CheckSquare className="h-4 w-4" />
              Tasks
            </TabsTrigger>
            <TabsTrigger value="context" className="flex items-center gap-2">
              <FolderOpen className="h-4 w-4" />
              Context
            </TabsTrigger>
          </TabsList>

          <TabsContent value="chat" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle>AI Agent Chat</CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <ChatPage />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="graph" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle>Graph Visualization</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-[600px] w-full">
                  <GraphPage />
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="sessions" className="mt-6">
            <SessionManager onSessionSelect={handleSessionSelect} />
          </TabsContent>

          <TabsContent value="tasks" className="mt-6">
            <TaskManager sessionId={contextSession?.session_id || null} />
          </TabsContent>

          <TabsContent value="context" className="mt-6">
            <ProjectContext sessionId={contextSession?.session_id || null} />
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
};