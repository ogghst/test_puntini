/**
 * Chat Input Component
 * 
 * Handles user input for sending messages in the chat interface.
 * Separated for reusability and single responsibility principle.
 */

import React from "react";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import type { ChatInputProps } from "./types";

/**
 * ChatInput component for message input and sending
 * 
 * @param props - Component props including value, handlers, and state
 * @returns JSX element representing the input area
 */
export const ChatInput: React.FC<ChatInputProps> = ({
  value,
  onChange,
  onSend,
  disabled = false,
  placeholder = "Type a message...",
  isLoading = false,
}) => {
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !disabled && !isLoading) {
      onSend();
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange(e.target.value);
  };

  const canSend = value.trim() !== "" && !disabled && !isLoading;

  return (
    <div className="flex items-center gap-4">
      <Input
        placeholder={placeholder}
        value={value}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        disabled={disabled || isLoading}
        className="flex-1"
      />
      <Button
        onClick={onSend}
        disabled={!canSend}
        className="px-6"
      >
        {isLoading ? "Sending..." : "Send"}
      </Button>
    </div>
  );
};
