import React, { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import { v4 as uuidv4 } from "uuid";
import { Avatar, AvatarFallback } from "../components/ui/avatar";
import { Button } from "../components/ui/button";
import { Card, CardContent } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { ScrollArea } from "../components/ui/scroll-area";
import {
  SessionAPIError,
  useMessages,
  useSession,
  type Message as SessionMessage,
} from "../utils/session";

// Define a type for the display message structure
interface DisplayMessage {
  id: string;
  text: string;
  source: string;
  type: string;
  timestamp: string;
}

const getAvatarForSource = (source: DisplayMessage["source"]) => {
  switch (source) {
    case "User":
      return "U";
    case "triage_agent":
      return "A";
    case "project_management_agent":
      return "P";
    case "thinking":
      return "T";
    case "log":
      return "L";
    case "debug":
      return "D";
    case "knowledge_graph_agent":
      return "K";
    default:
      return "?";
  }
};

const getCardColorForSource = (source: DisplayMessage["source"]) => {
  switch (source) {
    case "User":
      return "bg-primary text-primary-foreground";
    case "triage_agent":
      return "bg-secondary text-secondary-foreground";
    case "project_management_agent":
      return "bg-muted text-muted-foreground";
    case "knowledge_graph_agent":
      return "bg-accent text-accent-foreground";
    default:
      return "bg-card text-card-foreground";
  }
};

const ChatPage: React.FC = () => {
  const [displayMessages, setDisplayMessages] = useState<DisplayMessage[]>([]);
  const [input, setInput] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  // Use session management hooks
  const {
    currentSession,
    isLoading: sessionLoading,
    error: sessionError,
    createSession,
  } = useSession();
  const {
    messages: sessionMessages,
    sendMessage,
    isLoading: messageLoading,
  } = useMessages(currentSession?.session_id || null);

  // Create session on component mount
  useEffect(() => {
    const initializeSession = async () => {
      try {
        await createSession({
          user_id: "frontend_user",
          metadata: { source: "chat_page" },
        });
      } catch (err) {
        // console.error("Failed to create session:", err);
        setError(
          err instanceof SessionAPIError
            ? err.message
            : "Failed to create session"
        );
      }
    };

    initializeSession();
  }, [createSession]); // Include createSession in dependencies

  // Convert session messages to display messages
  useEffect(() => {
    const newDisplayMessages = sessionMessages.map(
      (msg: SessionMessage): DisplayMessage => {
        let content = "";
        let source = "User";
        let type = "AssistantMessage";

        if (msg.content) {
          if (typeof msg.content === "string") {
            content = msg.content;
          } else if (Array.isArray(msg.content)) {
            content = msg.content
              .map((item: unknown) =>
                typeof item === "string" ? item : JSON.stringify(item)
              )
              .join(" ");
          } else {
            content = JSON.stringify(msg.content);
          }
        }

        if (msg.message_type) {
          source = msg.message_type === "user" ? "User" : msg.message_type;
          type =
            msg.message_type === "user" ? "UserMessage" : "AssistantMessage";
        }

        return {
          id: msg.id,
          text: content,
          source: source,
          type: type,
          timestamp: msg.timestamp,
        };
      }
    );

    setDisplayMessages(newDisplayMessages);
  }, [sessionMessages]);

  // Add welcome message when session is created
  useEffect(() => {
    if (currentSession && displayMessages.length === 0) {
      const welcomeMessage: DisplayMessage = {
        id: uuidv4(),
        text: "Hello! How can I help you with your project today?",
        type: "triage_agent",
        source: "triage_agent",
        timestamp: new Date().toISOString(),
      };
      setDisplayMessages([welcomeMessage]);
    }
  }, [currentSession, displayMessages.length]);

  useEffect(() => {
    if (scrollAreaRef.current) {
      const scrollContainer = scrollAreaRef.current.querySelector(
        "[data-radix-scroll-area-viewport]"
      );
      if (scrollContainer) {
        scrollContainer.scrollTop = scrollContainer.scrollHeight;
      }
    }
  }, [displayMessages]);

  const handleSend = async () => {
    if (input.trim() !== "" && currentSession && !messageLoading) {
      try {
        // Add user message to display immediately
        const userMessage: DisplayMessage = {
          id: uuidv4(),
          text: input,
          type: "UserMessage",
          source: "User",
          timestamp: new Date().toISOString(),
        };
        setDisplayMessages((prev) => [...prev, userMessage]);

        // Send message to session
        await sendMessage({
          content: input,
          message_type: "user",
          metadata: { timestamp: new Date().toISOString() },
        });

        setInput("");
      } catch (err) {
        // console.error("Failed to send message:", err);
        setError(
          err instanceof SessionAPIError
            ? err.message
            : "Failed to send message"
        );
      }
    }
  };

  // Show loading state while creating session
  if (sessionLoading) {
    return (
      <div className="flex flex-col h-full p-4 items-center justify-center">
        <div className="text-lg">Creating session...</div>
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
        <Button onClick={() => window.location.reload()} className="mt-4">
          Retry
        </Button>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full p-4">
      <ScrollArea className="flex-grow mb-4" ref={scrollAreaRef}>
        <div className="space-y-4">
          {displayMessages.map((message) => (
            <div
              key={message.id}
              className={`flex items-start gap-4 ${
                message.source === "User" ? "justify-end" : "justify-start"
              }`}
            >
              {message.source !== "User" && message.type !== "debug" && (
                <Avatar>
                  <AvatarFallback>
                    {getAvatarForSource(message.source)}
                  </AvatarFallback>
                </Avatar>
              )}
              {message.type === "debug" ? (
                <div className="w-full bg-transparent text-green-600 font-mono text-xs p-2 rounded border-l-2 border-green-500">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-green-500">[DEBUG]</span>
                    <span className="text-gray-500">
                      {new Date().toLocaleTimeString()}
                    </span>
                    <span className="text-gray-400">|</span>
                    <span className="text-yellow-600">{message.source}</span>
                  </div>
                  <div className="text-green-600 whitespace-pre-wrap">
                    {message.text}
                  </div>
                </div>
              ) : (
                <Card
                  className={`w-3/4 ${getCardColorForSource(message.source)}`}
                >
                  <CardContent className="p-4">
                    <ReactMarkdown>{message.text}</ReactMarkdown>
                  </CardContent>
                </Card>
              )}
              {message.source === "User" && (
                <Avatar>
                  <AvatarFallback>
                    {getAvatarForSource(message.source)}
                  </AvatarFallback>
                </Avatar>
              )}
            </div>
          ))}
        </div>
      </ScrollArea>
      <div className="flex items-center gap-4">
        <Input
          placeholder="Type a message..."
          value={input}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
            setInput(e.target.value)
          }
          onKeyDown={(e: React.KeyboardEvent<HTMLInputElement>) => {
            if (e.key === "Enter") {
              handleSend();
            }
          }}
          disabled={messageLoading || !currentSession}
        />
        <Button
          onClick={handleSend}
          disabled={messageLoading || !currentSession}
        >
          Send
        </Button>
      </div>
    </div>
  );
};

export default ChatPage;
export { ChatPage };
