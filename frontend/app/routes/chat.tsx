import { Meta } from "react-router";
import { ChatPage } from "../chat/ChatPage";
import { ProtectedRoute } from "../components/auth/ProtectedRoute";
import type { Route } from "./+types/chat";

export function meta({}: Route.MetaArgs) {
  return [
    { title: "Chat" },
    {
      name: "description",
      content: "Chat with AI agents",
    },
  ];
}

export default function ChatPageRoute() {
  return (
    <>
      <Meta />
      <ProtectedRoute>
        <ChatPage />
      </ProtectedRoute>
    </>
  );
}
