/**
 * Chat Utilities
 * 
 * Utility functions for message transformation and styling.
 * Separated from components to follow single responsibility principle.
 */

import { v4 as uuidv4 } from "uuid";
import { type Message as SessionMessage } from "@/utils/session";
import type { 
  DisplayMessage, 
  MessageSource, 
  MessageType,
  MessageTransformers 
} from "./types";

/**
 * Transform a session message to display message format
 */
export const transformSessionMessage = (msg: SessionMessage): DisplayMessage => {
  let content = "";
  let source: MessageSource = "unknown";
  let type: MessageType = "OtherMessage";

  // Extract content based on message type
  if (msg.type === "user_prompt") {
    content = (msg.data?.prompt as string) || "";
    source = "User";
    type = "UserMessage";
  } else if (msg.type === "assistant_response") {
    content = (msg.data?.text as string) || "";
    source = "assistant_response";
    type = "AssistantMessage";
  } else if (msg.type === "reasoning") {
    const steps = msg.data?.steps;
    content = Array.isArray(steps) ? steps.join("\n") : JSON.stringify(msg.data);
    source = "reasoning";
    type = "ReasoningMessage";
  } else if (msg.type === "debug") {
    content = (msg.data?.message as string) || JSON.stringify(msg.data);
    source = "debug";
    type = "DebugMessage";
  } else if (msg.type === "error") {
    content = msg.error?.message || JSON.stringify(msg.error);
    source = "error";
    type = "ErrorMessage";
  } else {
    content = JSON.stringify(msg.data || msg);
    source = (msg.type as MessageSource) || "unknown";
    type = "OtherMessage";
  }

  return {
    id: uuidv4(),
    text: content,
    source,
    type,
    timestamp: msg.timestamp || new Date().toISOString(),
  };
};

/**
 * Get avatar character for message source
 */
export const getAvatarForSource = (source: MessageSource): string => {
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

/**
 * Get card color class for message source
 */
export const getCardColorForSource = (source: MessageSource): string => {
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

/**
 * Create a welcome message
 */
export const createWelcomeMessage = (text: string = "Hello! How can I help you with your project today?"): DisplayMessage => ({
  id: uuidv4(),
  text,
  type: "AssistantMessage",
  source: "assistant_response",
  timestamp: new Date().toISOString(),
});

/**
 * Create a user message for immediate display
 */
export const createUserMessage = (text: string): DisplayMessage => ({
  id: uuidv4(),
  text,
  type: "UserMessage",
  source: "User",
  timestamp: new Date().toISOString(),
});

/**
 * Message transformers object for easy access
 */
export const messageTransformers: MessageTransformers = {
  sessionToDisplay: transformSessionMessage,
  getAvatarForSource,
  getCardColorForSource,
};
