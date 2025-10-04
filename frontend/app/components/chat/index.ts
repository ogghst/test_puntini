/**
 * Chat Components Export
 * 
 * Centralized export for all chat-related components and utilities.
 * Provides clean imports for consumers of the chat system.
 */

// Main components
export { Chat } from "./Chat";
export { ChatMessage } from "./ChatMessage";
export { ChatMessages } from "./ChatMessages";
export { ChatInput } from "./ChatInput";

// Types
export type {
  DisplayMessage,
  MessageSource,
  MessageType,
  ChatProps,
  ChatMessageProps,
  ChatInputProps,
  ChatMessagesProps,
  MessageTransformers,
} from "./types";

// Utilities
export {
  transformSessionMessage,
  getAvatarForSource,
  getCardColorForSource,
  createWelcomeMessage,
  createUserMessage,
  messageTransformers,
} from "./utils";
