/**
 * Chat Component
 * 
 * Main chat interface component that orchestrates message display, input handling,
 * and session management. Follows React component composition patterns.
 */

import React, { useEffect, useState } from "react";
import { Button } from "../ui/button";
import { ChatInput } from "./ChatInput";
import { ChatMessages } from "./ChatMessages";
import { 
  useMessages, 
  useSession, 
  SessionAPIError
} from "@/utils/session";
import { useAuth } from "../auth/AuthContext";
import type { ChatProps, DisplayMessage } from "./types";
import { 
  transformSessionMessage, 
  createWelcomeMessage, 
  createUserMessage 
} from "./utils";

/**
 * Main Chat component that handles the complete chat interface
 * 
 * @param props - Component props including session configuration and callbacks
 * @returns JSX element representing the complete chat interface
 */
export const Chat: React.FC<ChatProps> = ({
  sessionId,
  onSessionCreated,
  onMessageSent,
  onError,
  welcomeMessage = "Hello! How can I help you with your project today?",
  showDebugMessages = true,
  inputPlaceholder = "Type a message...",
  disabled = false,
}) => {
  const [displayMessages, setDisplayMessages] = useState<DisplayMessage[]>([]);
  const [input, setInput] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const { user } = useAuth();

  // Session management hooks
  const {
    currentSession,
    isLoading: sessionLoading,
    error: sessionError,
    isConnected,
    createSession,
  } = useSession();

  const {
    messages: sessionMessages,
    sendMessage,
    isLoading: messageLoading,
  } = useMessages(currentSession?.session_id || sessionId || null);

  // Create session on component mount if no session provided and user is authenticated
  useEffect(() => {
    const initializeSession = async () => {
      if (!sessionId && !currentSession && !sessionLoading && user) {
        try {
          const newSession = await createSession({
            user_id: user?.username || "testuser",
            metadata: { source: "chat_component" },
          });
          
          if (onSessionCreated) {
            onSessionCreated(newSession.session_id);
          }
        } catch (err) {
          const errorMessage = err instanceof SessionAPIError 
            ? err.message 
            : "Failed to create session";
          
          setError(errorMessage);
          if (onError) {
            onError(errorMessage);
          }
        }
      }
    };

    initializeSession();
  }, [sessionId, currentSession, sessionLoading, createSession, user, onSessionCreated, onError]);

  // Convert session messages to display messages
  useEffect(() => {
    // Sort messages by timestamp to ensure chronological order
    const sortedMessages = [...sessionMessages].sort((a, b) => {
      const timestampA = new Date(a.timestamp || 0).getTime();
      const timestampB = new Date(b.timestamp || 0).getTime();
      return timestampA - timestampB;
    });
    
    const newDisplayMessages = sortedMessages.map(transformSessionMessage);
    setDisplayMessages(newDisplayMessages);
  }, [sessionMessages]);

  // Add welcome message when session is connected and no messages exist
  useEffect(() => {
    if (isConnected && sessionMessages.length === 0) {
      const welcome = createWelcomeMessage(welcomeMessage);
      setDisplayMessages([welcome]);
    }
  }, [isConnected, sessionMessages.length, welcomeMessage]);

  // Handle sending messages
  const handleSend = async () => {
    if (input.trim() === "" || !isConnected || messageLoading || disabled) {
      return;
    }

    try {
      // Send message to session - the session will handle adding it to the message list
      await sendMessage({
        content: input,
      });

      setInput("");
    } catch (err) {
      const errorMessage = err instanceof SessionAPIError 
        ? err.message 
        : "Failed to send message";
      
      setError(errorMessage);
      if (onError) {
        onError(errorMessage);
      }
    }
  };

  // Handle input change
  const handleInputChange = (value: string) => {
    setInput(value);
  };

  // Handle retry for errors
  const handleRetry = () => {
    window.location.reload();
  };

  // Show loading state while creating session
  if (sessionLoading) {
    return (
      <div className="flex flex-col h-full p-4 items-center justify-center">
        <div className="text-lg">Creating session...</div>
      </div>
    );
  }

  // Show authentication required message if user is not authenticated
  if (!user) {
    return (
      <div className="flex flex-col h-full p-4 items-center justify-center">
        <div className="text-lg text-gray-600">Please login to start chatting</div>
      </div>
    );
  }

  // Show error state
  if (sessionError || error) {
    return (
      <div className="flex flex-col h-full p-4 items-center justify-center">
        <div className="text-lg text-red-600">
          Error: {sessionError?.message || error}
        </div>
        <Button onClick={handleRetry} className="mt-4">
          Retry
        </Button>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full w-full max-h-screen">
      <div className="flex-1 min-h-0 w-full">
        <ChatMessages 
          messages={displayMessages}
          showDebugMessages={showDebugMessages}
        />
      </div>
      <div className="flex-shrink-0 p-4 border-t bg-background w-full">
        <ChatInput
          value={input}
          onChange={handleInputChange}
          onSend={handleSend}
          disabled={disabled || !isConnected}
          placeholder={inputPlaceholder}
          isLoading={messageLoading}
        />
      </div>
    </div>
  );
};
