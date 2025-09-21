import { useEffect, useRef, useState } from "react";
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
} from "@/utils/session";
import { useAuth } from "../components/auth/AuthContext";

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
    case "assistant_response":
      return "A";
    case "reasoning":
      return "R";
    case "debug":
      return "D";
    case "error":
      return "E";
    default:
      return source.charAt(0).toUpperCase();
  }
};

const getCardColorForSource = (source: DisplayMessage["source"]) => {
  switch (source) {
    case "User":
      return "bg-primary text-primary-foreground";
    case "assistant_response":
      return "bg-secondary text-secondary-foreground";
    case "reasoning":
      return "bg-muted text-muted-foreground";
    case "debug":
      return "bg-accent text-accent-foreground";
    case "error":
      return "bg-destructive text-destructive-foreground";
    default:
      return "bg-card text-card-foreground";
  }
};

const ChatPage: React.FC = () => {
  const [displayMessages, setDisplayMessages] = useState<DisplayMessage[]>([]);
  const [input, setInput] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const { user } = useAuth();

  // Use session management hooks
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
  } = useMessages(currentSession?.session_id || null);

  // Create session on component mount
  useEffect(() => {
    const initializeSession = async () => {
      try {
        await createSession({
          user_id: user?.username || "testuser",
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
  }, [createSession, user]); // Include createSession and user in dependencies

  // Convert session messages to display messages
  useEffect(() => {
    const newDisplayMessages = sessionMessages.map(
      (msg: SessionMessage): DisplayMessage => {
        let content = "";
        let source = "unknown";
        let type = "message";

        // Extract content based on message type
        if (msg.type === "user_prompt") {
          content = msg.data?.prompt || "";
          source = "User";
          type = "UserMessage";
        } else if (msg.type === "assistant_response") {
          content = msg.data?.text || "";
          source = "assistant_response";
          type = "AssistantMessage";
        } else if (msg.type === "reasoning") {
          content = msg.data?.steps?.join("\n") || JSON.stringify(msg.data);
          source = "reasoning";
          type = "ReasoningMessage";
        } else if (msg.type === "debug") {
          content = msg.data?.message || JSON.stringify(msg.data);
          source = "debug";
          type = "DebugMessage";
        } else if (msg.type === "error") {
          content = msg.error?.message || JSON.stringify(msg.error);
          source = "error";
          type = "ErrorMessage";
        } else {
          content = JSON.stringify(msg.data || msg);
          source = msg.type || "unknown";
          type = "OtherMessage";
        }

        return {
          id: uuidv4(),
          text: content,
          source: source,
          type: type,
          timestamp: msg.timestamp || new Date().toISOString(),
        };
      }
    );

    setDisplayMessages(newDisplayMessages);
  }, [sessionMessages]);

  // Add welcome message when session is created
  useEffect(() => {
    if (isConnected && displayMessages.length === 0) {
      const welcomeMessage: DisplayMessage = {
        id: uuidv4(),
        text: "Hello! How can I help you with your project today?",
        type: "assistant_response",
        source: "assistant_response",
        timestamp: new Date().toISOString(),
      };
      setDisplayMessages([welcomeMessage]);
    }
  }, [isConnected, displayMessages.length]);

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
    if (input.trim() !== "" && isConnected && !messageLoading) {
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
          disabled={messageLoading || !isConnected}
        />
        <Button
          onClick={handleSend}
          disabled={messageLoading || !isConnected}
        >
          Send
        </Button>
      </div>
    </div>
  );
};

export default ChatPage;
export { ChatPage };
