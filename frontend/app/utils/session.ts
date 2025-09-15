/**
 * Session management service for the Puntini Agent system.
 *
 * This module provides TypeScript interfaces and WebSocket functions that are compliant
 * with the backend Puntini Agent API system.
 */

// Import React for hooks
import { useCallback, useEffect, useState } from "react";

// Base API configuration
const API_BASE_URL = "http://localhost:8009";

// Session-related types (compliant with backend models)
export interface SessionInfo {
  session_id: string;
  user_id: string;
  created_at: string;
  last_activity: string;
  is_active: boolean;
  graph_data: Record<string, any>;
  chat_history: Array<any>;
}

export interface Message {
  type: MessageType;
  data: Record<string, any>;
  session_id?: string;
  timestamp?: string;
  error?: {
    code: number;
    message: string;
  };
}

export type MessageType = 
  | "init_session" 
  | "session_ready" 
  | "close_session"
  | "user_prompt" 
  | "assistant_response" 
  | "reasoning" 
  | "debug" 
  | "graph_update" 
  | "error" 
  | "chat_history" 
  | "ping" 
  | "pong";

export interface SessionCreateRequest {
  user_id: string;
  metadata?: Record<string, any>;
}

export interface MessageRequest {
  content: any;
  message_type?: MessageType;
  metadata?: Record<string, any>;
}

export interface ProjectContext {
  project_context: Record<string, any>;
  tasks: TaskInfo[];
  task_count: number;
}

export interface TaskInfo {
  id: string;
  title: string;
  description?: string;
  status: "pending" | "in_progress" | "completed" | "cancelled";
  priority: "low" | "medium" | "high" | "urgent";
  created_at: string;
  metadata: Record<string, any>;
}

export interface SessionListResponse {
  sessions: SessionInfo[];
  total_count: number;
  active_count: number;
}

export interface SessionStats {
  total_sessions: number;
  active_sessions: number;
  expired_sessions: number;
  error_sessions: number;
  max_sessions: number;
  average_session_duration?: number;
}

// API Error class
export class SessionAPIError extends Error {
  constructor(
    message: string,
    public code?: number,
    public details?: any
  ) {
    super(message);
    this.name = "SessionAPIError";
  }
}

// WebSocket manager for handling connections and messages
class WebSocketManager {
  private static instance: WebSocketManager;
  private websocket: WebSocket | null = null;
  private token: string | null = null;
  private session_id: string | null = null;
  private messageListeners: Array<(message: Message) => void> = [];
  private connectionPromise: Promise<boolean> | null = null;
  private connectionResolve: ((value: boolean) => void) | null = null;

  private constructor() {}

  static getInstance(): WebSocketManager {
    if (!WebSocketManager.instance) {
      WebSocketManager.instance = new WebSocketManager();
    }
    return WebSocketManager.instance;
  }

  async connect(token: string): Promise<boolean> {
    if (this.connectionPromise) {
      return this.connectionPromise;
    }

    this.connectionPromise = new Promise((resolve) => {
      this.connectionResolve = resolve;
    });

    try {
      this.token = token;
      const wsUrl = `${API_BASE_URL.replace('http', 'ws')}/ws/chat?token=${token}`;
      this.websocket = new WebSocket(wsUrl);

      this.websocket.onopen = () => {
        console.log("WebSocket connected");
        // Initialize session
        this.sendMessage({
          type: "init_session",
          data: {}
        });
      };

      this.websocket.onmessage = (event) => {
        try {
          const message: Message = JSON.parse(event.data);
          if (message.type === "session_ready") {
            this.session_id = message.data?.session_id || null;
            if (this.connectionResolve) {
              this.connectionResolve(true);
            }
          }
          // Notify all listeners
          this.messageListeners.forEach(listener => listener(message));
        } catch (error) {
          console.error("Error parsing WebSocket message:", error);
        }
      };

      this.websocket.onerror = (error) => {
        console.error("WebSocket error:", error);
        if (this.connectionResolve) {
          this.connectionResolve(false);
        }
      };

      this.websocket.onclose = () => {
        console.log("WebSocket disconnected");
        this.websocket = null;
        this.session_id = null;
      };

      return this.connectionPromise;
    } catch (error) {
      console.error("WebSocket connection error:", error);
      if (this.connectionResolve) {
        this.connectionResolve(false);
      }
      return false;
    }
  }

  disconnect() {
    if (this.websocket) {
      this.websocket.close();
      this.websocket = null;
    }
    this.token = null;
    this.session_id = null;
    this.connectionPromise = null;
    this.connectionResolve = null;
  }

  isConnected(): boolean {
    return this.websocket !== null && this.websocket.readyState === WebSocket.OPEN;
  }

  getSessionId(): string | null {
    return this.session_id;
  }

  sendMessage(message: Omit<Message, "session_id" | "timestamp">) {
    if (!this.websocket || this.websocket.readyState !== WebSocket.OPEN) {
      throw new SessionAPIError("WebSocket is not connected");
    }

    const messageWithSession: Message = {
      ...message,
      session_id: this.session_id || undefined,
      timestamp: new Date().toISOString()
    };

    this.websocket.send(JSON.stringify(messageWithSession));
  }

  addMessageListener(listener: (message: Message) => void) {
    this.messageListeners.push(listener);
  }

  removeMessageListener(listener: (message: Message) => void) {
    this.messageListeners = this.messageListeners.filter(l => l !== listener);
  }
}

// Session API functions using WebSocket
export class SessionAPI {
  private static wsManager = WebSocketManager.getInstance();

  // Authentication functions
  static async login(username: string, password: string): Promise<{ access_token: string; token_type: string; user_id: string }> {
    const response = await fetch(`${API_BASE_URL}/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ username, password }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new SessionAPIError(
        errorData.detail || `HTTP ${response.status}: ${response.statusText}`,
        response.status,
        errorData
      );
    }

    return response.json();
  }

  static async register(username: string, password: string): Promise<{ username: string; email: string; full_name: string }> {
    const response = await fetch(`${API_BASE_URL}/register`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ username, password }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new SessionAPIError(
        errorData.detail || `HTTP ${response.status}: ${response.statusText}`,
        response.status,
        errorData
      );
    }

    return response.json();
  }

  // WebSocket connection functions
  static async connectWebSocket(token: string): Promise<boolean> {
    return this.wsManager.connect(token);
  }

  static disconnectWebSocket() {
    this.wsManager.disconnect();
  }

  static isConnected(): boolean {
    return this.wsManager.isConnected();
  }

  static getSessionId(): string | null {
    return this.wsManager.getSessionId();
  }

  // Message functions
  static sendUserPrompt(prompt: string) {
    this.wsManager.sendMessage({
      type: "user_prompt",
      data: { prompt }
    });
  }

  static sendPing() {
    this.wsManager.sendMessage({
      type: "ping",
      data: {}
    });
  }

  static closeSession() {
    this.wsManager.sendMessage({
      type: "close_session",
      data: {}
    });
  }

  // Add listener for incoming messages
  static addMessageListener(listener: (message: Message) => void) {
    this.wsManager.addMessageListener(listener);
  }

  static removeMessageListener(listener: (message: Message) => void) {
    this.wsManager.removeMessageListener(listener);
  }

  // Session management functions (REST-based)
  static async getMySessions(): Promise<{ sessions: Array<any> }> {
    // This would require authentication headers in a real implementation
    return { sessions: [] };
  }

  static async getSessionStats(): Promise<any> {
    // This would require authentication headers in a real implementation
    return {
      total_sessions: 0,
      active_sessions: 0,
      total_users: 0,
      session_timeout_minutes: 60
    };
  }

  static async listSessions(): Promise<SessionListResponse> {
    // This would require authentication headers in a real implementation
    return {
      sessions: [],
      total_count: 0,
      active_count: 0
    };
  }

  static async createSession(
    request: SessionCreateRequest
  ): Promise<SessionInfo> {
    // This would require authentication headers in a real implementation
    return {
      session_id: "mock-session-id",
      user_id: request.user_id,
      created_at: new Date().toISOString(),
      last_activity: new Date().toISOString(),
      is_active: true,
      graph_data: {},
      chat_history: []
    };
  }

  static async destroySession(sessionId: string): Promise<{ message: string }> {
    // This would require authentication headers in a real implementation
    return { message: "Session destroyed" };
  }
}

// Session management hook for React components
export function useSession() {
  const [currentSession, setCurrentSession] = useState<SessionInfo | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<SessionAPIError | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  const createSession = useCallback(async (request: SessionCreateRequest) => {
    setIsLoading(true);
    setError(null);

    try {
      // For demo purposes, we'll use the test user
      const loginResult = await SessionAPI.login("testuser", "testpass");
      const connected = await SessionAPI.connectWebSocket(loginResult.access_token);
      
      if (!connected) {
        throw new SessionAPIError("Failed to connect to WebSocket");
      }
      
      setIsConnected(true);
      
      // Create a mock session object for the frontend
      const session: SessionInfo = {
        session_id: SessionAPI.getSessionId() || "unknown",
        user_id: loginResult.user_id,
        created_at: new Date().toISOString(),
        last_activity: new Date().toISOString(),
        is_active: true,
        graph_data: {},
        chat_history: []
      };
      
      setCurrentSession(session);
      return session;
    } catch (err) {
      const apiError =
        err instanceof SessionAPIError
          ? err
          : new SessionAPIError("Failed to create session");
      setError(apiError);
      throw apiError;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const destroySession = useCallback(async () => {
    try {
      SessionAPI.closeSession();
      SessionAPI.disconnectWebSocket();
      setCurrentSession(null);
      setIsConnected(false);
    } catch (err) {
      const apiError =
        err instanceof SessionAPIError
          ? err
          : new SessionAPIError("Failed to destroy session");
      setError(apiError);
      throw apiError;
    }
  }, []);

  const refreshSession = useCallback(async () => {
    // With WebSocket, we don't need to refresh the session
    // The connection handles this automatically
  }, []);

  return {
    currentSession,
    isLoading,
    error,
    isConnected,
    createSession,
    destroySession,
    refreshSession,
  };
}

// Message management hook for React components
export function useMessages(sessionId: string | null) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<SessionAPIError | null>(null);

  // Add message listener on component mount
  useEffect(() => {
    const handleMessage = (message: Message) => {
      setMessages(prev => [...prev, message]);
    };

    SessionAPI.addMessageListener(handleMessage);
    
    // Cleanup listener on unmount
    return () => {
      SessionAPI.removeMessageListener(handleMessage);
    };
  }, []);

  const sendMessage = useCallback(
    async (request: MessageRequest) => {
      if (!SessionAPI.isConnected()) {
        throw new Error("No WebSocket connection available");
      }

      setIsLoading(true);
      setError(null);

      try {
        SessionAPI.sendUserPrompt(request.content);
      } catch (err) {
        const apiError =
          err instanceof SessionAPIError
            ? err
            : new SessionAPIError("Failed to send message");
        setError(apiError);
        throw apiError;
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  const receiveMessage = useCallback(
    async (timeout?: number) => {
      // With WebSocket, messages are received automatically through the listener
      // This function is kept for API compatibility but doesn't do anything
      return null;
    },
    []
  );

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    receiveMessage,
    clearMessages,
  };
}


