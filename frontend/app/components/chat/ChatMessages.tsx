/**
 * Chat Messages Component
 * 
 * Renders a scrollable list of chat messages with auto-scroll functionality.
 * Separated from Chat component for better modularity.
 */

import React, { useEffect, useRef } from "react";
import { ScrollArea } from "../ui/scroll-area";
import { ChatMessage } from "./ChatMessage";
import type { ChatMessagesProps } from "./types";
import { type Message as SessionMessage } from "@/utils/session";

/**
 * ChatMessages component for rendering the message list
 * 
 * @param props - Component props including messages array and display options
 * @returns JSX element representing the scrollable message list
 */
export const ChatMessages: React.FC<ChatMessagesProps> = ({ 
  messages, 
  showDebugMessages = true,
  originalMessages = []
}) => {
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollTop = scrollContainerRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <div className="h-full w-full flex flex-col">
      <ScrollArea className="flex-1 w-full">
        <div 
          ref={scrollContainerRef}
          className="space-y-4 p-4 w-full"
        >
          {messages.map((message, index) => (
            <ChatMessage
              key={message.id}
              message={message}
              showDebugMessages={showDebugMessages}
              originalMessage={originalMessages[index]}
            />
          ))}
        </div>
      </ScrollArea>
    </div>
  );
};
