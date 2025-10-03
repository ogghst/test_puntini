import { Meta } from "react-router";
import { Dashboard } from "../components/dashboard/Dashboard";
import { ProtectedRoute } from "../components/auth/ProtectedRoute";
import type { Route } from "./+types/dashboard";

export function meta({}: Route.MetaArgs) {
  return [
    { title: "Dashboard - Puntini" },
    {
      name: "description",
      content: "Manage your requests with AI agents",
    },
  ];
}

export default function DashboardPage() {
  return (
    <>
      <Meta />
      <ProtectedRoute>
        <Dashboard />
      </ProtectedRoute>
    </>
  );
}
