import { Meta } from "react-router";
import { ChatPage } from "../chat/ChatPage";
import type { Route } from "./+types/chat";

export function meta({}: Route.MetaArgs) {
  return [
    { title: "Chat - Business Improvement Project Management" },
    {
      name: "description",
      content: "Chat with AI agents for project management",
    },
  ];
}

export default function ChatPageRoute() {
  return (
    <>
      <Meta />
      <ChatPage />
    </>
  );
}
