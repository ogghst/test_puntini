import { Meta } from "react-router";
import { Dashboard } from "../components/dashboard/Dashboard";
import type { Route } from "./+types/dashboard";

export function meta({}: Route.MetaArgs) {
  return [
    { title: "Dashboard - Business Improvement Project Management" },
    {
      name: "description",
      content: "Manage your business improvement projects with AI agents",
    },
  ];
}

export default function DashboardPage() {
  return (
    <>
      <Meta />
      <Dashboard />
    </>
  );
}
