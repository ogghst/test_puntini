/**
 * Session management service for the Puntini Agent system.
 *
 * This module provides TypeScript interfaces and WebSocket functions that are compliant
 * with the backend Puntini Agent API system.
 */

// Import React for hooks
import { useCallback, useEffect, useState } from "react";
import { config, getApiUrl, getWebSocketEndpoint } from "./config";

// Session-related types (compliant with backend models)
export interface SessionInfo {
  session_id: string;
  user_id: string;
  created_at: string;
  last_activity: string;
  is_active: boolean;
  graph_data: Record<string, unknown>;
  chat_history: Array<unknown>;
}

export interface Message {
  type: MessageType;
  data: Record<string, unknown>;
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
  metadata?: Record<string, unknown>;
}

export interface MessageRequest {
  content: unknown;
  message_type?: MessageType;
  metadata?: Record<string, unknown>;
}

export interface ProjectContext {
  project_context: Record<string, unknown>;
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
  metadata: Record<string, unknown>;
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
    public details?: unknown
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
  private reconnectAttempts: number = 0;
  private heartbeatInterval: NodeJS.Timeout | null = null;

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
      const wsConfig = config.getWebSocketConfig();
      const wsUrl = `${getWebSocketEndpoint('/ws/chat')}?token=${token}`;
      
      if (config.isDebugMode()) {
        // eslint-disable-next-line no-console
        console.log("Connecting to WebSocket:", wsUrl);
      }
      
      this.websocket = new WebSocket(wsUrl);

      this.websocket.onopen = () => {
        // eslint-disable-next-line no-console
        console.log("WebSocket connected");
        this.reconnectAttempts = 0;
        
        // Start heartbeat
        this.startHeartbeat();
        
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
            this.session_id = (message.data?.session_id as string) || null;
            if (this.connectionResolve) {
              this.connectionResolve(true);
            }
          } else if (message.type === "pong") {
            // Heartbeat response received
            if (config.isDebugMode()) {
              // eslint-disable-next-line no-console
              console.log("Heartbeat pong received");
            }
          }
          
          // Notify all listeners
          this.messageListeners.forEach(listener => listener(message));
        } catch (error) {
          // eslint-disable-next-line no-console
          console.error("Error parsing WebSocket message:", error);
        }
      };

      this.websocket.onerror = (error) => {
        // eslint-disable-next-line no-console
        console.error("WebSocket error:", error);
        if (this.connectionResolve) {
          this.connectionResolve(false);
        }
      };

      this.websocket.onclose = () => {
        // eslint-disable-next-line no-console
        console.log("WebSocket disconnected");
        this.stopHeartbeat();
        this.websocket = null;
        this.session_id = null;
        
        // Attempt reconnection if not manually disconnected
        if (this.token && this.reconnectAttempts < wsConfig.reconnectAttempts) {
          this.reconnectAttempts++;
          // eslint-disable-next-line no-console
          console.log(`Attempting to reconnect (${this.reconnectAttempts}/${wsConfig.reconnectAttempts})...`);
          setTimeout(() => {
            if (this.token) {
              this.connect(this.token);
            }
          }, wsConfig.reconnectDelay);
        }
      };

      return this.connectionPromise;
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error("WebSocket connection error:", error);
      if (this.connectionResolve) {
        this.connectionResolve(false);
      }
      return false;
    }
  }

  disconnect() {
    this.stopHeartbeat();
    if (this.websocket) {
      this.websocket.close();
      this.websocket = null;
    }
    this.token = null;
    this.session_id = null;
    this.connectionPromise = null;
    this.connectionResolve = null;
    this.reconnectAttempts = 0;
  }

  private startHeartbeat() {
    const wsConfig = config.getWebSocketConfig();
    this.heartbeatInterval = setInterval(() => {
      if (this.isConnected()) {
        this.sendMessage({
          type: "ping",
          data: {}
        });
      }
    }, wsConfig.heartbeatInterval);
  }

  private stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
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
    const response = await fetch(getApiUrl('/login'), {
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
    const response = await fetch(getApiUrl('/register'), {
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
  static async getMySessions(): Promise<{ sessions: Array<unknown> }> {
    // This would require authentication headers in a real implementation
    return { sessions: [] };
  }

  static async getSessionStats(): Promise<unknown> {
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

  static async destroySession(_sessionId: string): Promise<{ message: string }> {
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

  const createSession = useCallback(async (_request: SessionCreateRequest) => {
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
export function useMessages(_sessionId: string | null) {
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
    async (_request: MessageRequest) => {
      if (!SessionAPI.isConnected()) {
        throw new Error("No WebSocket connection available");
      }

      setIsLoading(true);
      setError(null);

      try {
        SessionAPI.sendUserPrompt(_request.content as string);
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
    async (_timeout?: number) => {
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

// Log configuration on module load
if (config.isDebugMode()) {
  config.logConfiguration();
}


