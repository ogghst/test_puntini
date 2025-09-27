# Chat Components

This directory contains the refactored chat system components, following React best practices for component separation and reusability.

## Architecture

The chat system has been refactored into separate, focused components:

### Core Components

- **`Chat.tsx`** - Main chat component that orchestrates all chat functionality
- **`ChatMessage.tsx`** - Individual message rendering component
- **`ChatMessages.tsx`** - Scrollable message list container
- **`ChatInput.tsx`** - Message input and sending component

### Supporting Files

- **`types.ts`** - TypeScript interfaces and type definitions
- **`utils.ts`** - Utility functions for message transformation and styling
- **`index.ts`** - Centralized exports for clean imports

## Component Separation Benefits

Following React best practices, this architecture provides:

1. **Single Responsibility** - Each component has one clear purpose
2. **Reusability** - Components can be used independently in different contexts
3. **Testability** - Smaller components are easier to test
4. **Maintainability** - Changes to one component don't affect others
5. **Type Safety** - Comprehensive TypeScript interfaces

## Usage

### Basic Usage

```tsx
import { Chat } from "../components/chat";

function ChatPage() {
  return (
    <Chat
      welcomeMessage="Hello! How can I help you?"
      showDebugMessages={true}
    />
  );
}
```

### Advanced Usage

```tsx
import { Chat, ChatMessage, ChatMessages, ChatInput } from "../components/chat";

function CustomChatInterface() {
  return (
    <div>
      <ChatMessages messages={messages} />
      <ChatInput 
        value={input}
        onChange={setInput}
        onSend={handleSend}
      />
    </div>
  );
}
```

## Props

### Chat Component Props

- `sessionId?: string | null` - Optional session ID
- `onSessionCreated?: (sessionId: string) => void` - Session creation callback
- `onMessageSent?: (message: DisplayMessage) => void` - Message sent callback
- `onError?: (error: string) => void` - Error callback
- `welcomeMessage?: string` - Custom welcome message
- `showDebugMessages?: boolean` - Show/hide debug messages
- `inputPlaceholder?: string` - Input placeholder text
- `disabled?: boolean` - Disable chat functionality

## Migration from ChatPage

The original `ChatPage.tsx` has been simplified to use the new `Chat` component:

**Before:**
```tsx
// 300+ lines of mixed concerns
const ChatPage = () => {
  // Session management
  // Message transformation
  // UI rendering
  // Input handling
  // Error handling
  // ...
};
```

**After:**
```tsx
// 15 lines focused on page-level concerns
const ChatPage = () => {
  return (
    <Chat
      welcomeMessage="Hello! How can I help you with your project today?"
      showDebugMessages={true}
      inputPlaceholder="Type a message..."
    />
  );
};
```

## Design Patterns Applied

1. **Component Composition** - Building complex UI from simple components
2. **Separation of Concerns** - Logic, presentation, and data separated
3. **Props Interface** - Clear contracts between components
4. **Custom Hooks** - Session and message management abstracted
5. **Type Safety** - Comprehensive TypeScript coverage
6. **Error Boundaries** - Graceful error handling
7. **Accessibility** - Proper ARIA attributes and keyboard navigation

This refactoring makes the chat system more maintainable, testable, and reusable across the application.
