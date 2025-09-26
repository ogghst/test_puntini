/**
 * Chat Message Component
 * 
 * Renders individual chat messages with appropriate styling and avatars.
 * Follows React component separation best practices.
 */

import React from "react";
import ReactMarkdown from "react-markdown";
import { Avatar, AvatarFallback } from "../ui/avatar";
import { Card, CardContent } from "../ui/card";
import type { ChatMessageProps } from "./types";
import { getAvatarForSource, getCardColorForSource } from "./utils";

/**
 * ChatMessage component for rendering individual messages
 * 
 * @param props - Component props including message data and display options
 * @returns JSX element representing a single chat message
 */
export const ChatMessage: React.FC<ChatMessageProps> = ({ 
  message, 
  showDebugMessages = true 
}) => {

  // Don't render debug messages if they're disabled
  if (message.type === "DebugMessage" && !showDebugMessages) {
    return null;
  }

  const isUserMessage = message.source === "User";
  const isDebugMessage = message.type === "DebugMessage";

  return (
    <div
      className={`flex items-start gap-4 ${
        isUserMessage ? "justify-end" : "justify-start"
      }`}
    >
      {/* Avatar for non-user messages (except debug) */}
      {!isUserMessage && !isDebugMessage && (
        <Avatar>
          <AvatarFallback>
            {getAvatarForSource(message.source)}
          </AvatarFallback>
        </Avatar>
      )}

      {/* Message content */}
      {isDebugMessage ? (
        <div className="w-full bg-transparent text-green-600 font-mono text-xs p-2 rounded border-l-2 border-green-500">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-green-500">[DEBUG]</span>
            <span className="text-gray-500">
              {new Date(message.timestamp).toLocaleTimeString()}
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

      {/* Avatar for user messages */}
      {isUserMessage && (
        <Avatar>
          <AvatarFallback>
            {getAvatarForSource(message.source)}
          </AvatarFallback>
        </Avatar>
      )}
    </div>
  );
};
