/**
 * Chat Component Types
 * 
 * Defines TypeScript interfaces and types for the chat system components.
 * Following React best practices for component separation and type safety.
 */

import { type Message as SessionMessage } from "@/utils/session";

/**
 * Display message structure for the chat UI
 */
export interface DisplayMessage {
  id: string;
  text: string;
  source: MessageSource;
  type: MessageType;
  timestamp: string;
}

/**
 * Message source types for avatar and styling
 */
export type MessageSource = 
  | "User"
  | "assistant_response"
  | "reasoning"
  | "debug"
  | "error"
  | "unknown";

/**
 * Message type categories
 */
export type MessageType = 
  | "UserMessage"
  | "AssistantMessage"
  | "ReasoningMessage"
  | "DebugMessage"
  | "ErrorMessage"
  | "OtherMessage";

/**
 * Props for the main Chat component
 */
export interface ChatProps {
  /** Session ID for the chat */
  sessionId?: string | null;
  /** Callback when session is created */
  onSessionCreated?: (sessionId: string) => void;
  /** Callback when message is sent */
  onMessageSent?: (message: DisplayMessage) => void;
  /** Callback when error occurs */
  onError?: (error: string) => void;
  /** Custom welcome message */
  welcomeMessage?: string;
  /** Whether to show debug messages */
  showDebugMessages?: boolean;
  /** Custom placeholder for input */
  inputPlaceholder?: string;
  /** Whether the chat is disabled */
  disabled?: boolean;
}

/**
 * Props for the ChatMessage component
 */
export interface ChatMessageProps {
  message: DisplayMessage;
  showDebugMessages?: boolean;
}

/**
 * Props for the ChatInput component
 */
export interface ChatInputProps {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  disabled?: boolean;
  placeholder?: string;
  isLoading?: boolean;
}

/**
 * Props for the ChatMessages component
 */
export interface ChatMessagesProps {
  messages: DisplayMessage[];
  showDebugMessages?: boolean;
}

/**
 * Message transformation utilities
 */
export interface MessageTransformers {
  sessionToDisplay: (msg: SessionMessage) => DisplayMessage;
  getAvatarForSource: (source: MessageSource) => string;
  getCardColorForSource: (source: MessageSource) => string;
}
