/**
 * Chat Page Component
 * 
 * Page-level component that uses the reusable Chat component.
 * Demonstrates clean separation between page logic and component logic.
 */

import React from "react";
import { Chat } from "../components/chat";

/**
 * ChatPage component - simplified to use the extracted Chat component
 * 
 * @returns JSX element representing the chat page
 */
const ChatPage: React.FC = () => {
  return (
    <div className="h-full w-full">
      <Chat
        welcomeMessage="Hello! How can I help you with your project today?"
        showDebugMessages={false}
        inputPlaceholder="Type a message..."
      />
    </div>
  );
};

export default ChatPage;
export { ChatPage };
