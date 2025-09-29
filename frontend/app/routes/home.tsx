import { Activity, CheckSquare, MessageSquare, Users } from "lucide-react";
import { Link, Meta } from "react-router";
import { Button } from "../components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../components/ui/card";
import { useAuth } from "../components/auth/AuthContext";
import type { Route } from "./+types/home";

export function meta({}: Route.MetaArgs) {
  return [
    { title: "Puntini" },
    {
      name: "description",
      content:
        "AI-powered system for knowledge graph manipulation",
    },
  ];
}

export default function Home() {
  const { isAuthenticated, logout } = useAuth();

  return (
    <>
      <Meta />
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              <div className="flex items-center gap-2">
                <Activity className="h-8 w-8 text-blue-600" />
                <h1 className="text-xl font-bold text-gray-900">
                  Puntini
                </h1>
              </div>
              <div className="flex items-center gap-4">
                {isAuthenticated ? (
                  <>
                    <Link to="/dashboard">
                      <Button>Dashboard</Button>
                    </Link>
                    <Button variant="outline" onClick={logout}>
                      Logout
                    </Button>
                  </>
                ) : (
                  <Link to="/login">
                    <Button>Login</Button>
                  </Link>
                )}
              </div>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">
              Welcome to Puntini
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Leverage AI agents to manage your knowledge graphs
            </p>
          </div>

          {/* Features Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MessageSquare className="h-5 w-5 text-blue-600" />
                  AI Chat
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600">
                  Interact with specialized AI agents for project management,
                  triage, and knowledge graph operations.
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Users className="h-5 w-5 text-green-600" />
                  Session Management
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600">
                  Manage user sessions with automatic agent registration and
                  real-time message routing.
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="h-5 w-5 text-purple-600" />
                  Project Context
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600">
                  Maintain project-specific state and context across all your
                  improvement initiatives.
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <CheckSquare className="h-5 w-5 text-orange-600" />
                  Task Management
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600">
                  Create, track, and manage tasks with priority levels and
                  status tracking.
                </p>
              </CardContent>
            </Card>
          </div>

          {/* CTA Section */}
          <div className="text-center">
            <Card className="max-w-2xl mx-auto">
              <CardHeader>
                <CardTitle>Get Started</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-gray-600">
                  Ready to start managing your business improvement projects
                  with AI?
                </p>
                <div className="flex gap-4 justify-center">
                  {isAuthenticated ? (
                    <Link to="/dashboard">
                      <Button size="lg">Open Dashboard</Button>
                    </Link>
                  ) : (
                    <Link to="/login">
                      <Button size="lg">Login to Get Started</Button>
                    </Link>
                  )}
                  <Link to="/chat">
                    <Button variant="outline" size="lg">
                      Start Chatting
                    </Button>
                  </Link>
                </div>
              </CardContent>
            </Card>
          </div>
        </main>

        {/* Footer */}
        <footer className="bg-white border-t border-gray-200 mt-16">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="text-center text-gray-600">
              <p>
                &copy; 2025 Nicola Muratori. All rights
                reserved.
              </p>
            </div>
          </div>
        </footer>
      </div>
    </>
  );
}
