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
  status?: string;
  agent_count?: number;
  task_count?: number;
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
  | "state_update"
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

// State update message interfaces
export interface StateUpdateData {
  update_type: string;
  current_step: string;
  todo_list: TodoItem[];
  entities_created: EntityInfo[];
  progress?: string[];
  artifacts?: unknown[];
  failures?: unknown[];
}

export interface TodoItem {
  description: string;
  status: "planned" | "done";
  step_number?: number;
  tool_name?: string;
  estimated_complexity?: "low" | "medium" | "high";
}

export interface EntityInfo {
  name: string;
  type: string;
  label: string;
  properties: Record<string, unknown>;
  confidence: number;
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
  static async getMySessions(): Promise<{ sessions: SessionInfo[] }> {
    const token = this.getStoredToken();
    if (!token) {
      throw new SessionAPIError("No authentication token found");
    }

    const response = await fetch(getApiUrl('/sessions/my'), {
      method: "GET",
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new SessionAPIError(
        errorData.detail || `HTTP ${response.status}: ${response.statusText}`,
        response.status,
        errorData
      );
    }

    const data = await response.json();
    return {
      sessions: data.sessions.map((session: Record<string, unknown>) => ({
        session_id: session.session_id,
        user_id: session.user_id,
        created_at: session.created_at,
        last_activity: session.last_activity,
        is_active: session.is_active,
        graph_data: session.graph_data || {},
        chat_history: session.chat_history || [],
        status: this.determineSessionStatus(session),
        agent_count: this.extractAgentCount(session),
        task_count: this.extractTaskCount(session)
      }))
    };
  }

  static async getSessionStats(): Promise<SessionStats> {
    const token = this.getStoredToken();
    if (!token) {
      throw new SessionAPIError("No authentication token found");
    }

    const response = await fetch(getApiUrl('/sessions/stats'), {
      method: "GET",
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new SessionAPIError(
        errorData.detail || `HTTP ${response.status}: ${response.statusText}`,
        response.status,
        errorData
      );
    }

    const data = await response.json();
    return {
      total_sessions: data.total_sessions,
      active_sessions: data.active_sessions,
      expired_sessions: data.total_sessions - data.active_sessions,
      error_sessions: 0, // Backend doesn't track error sessions separately
      max_sessions: 10, // Default value
      average_session_duration: 45 // Default value
    };
  }

  static async listSessions(): Promise<SessionListResponse> {
    const sessionsData = await this.getMySessions();
    return {
      sessions: sessionsData.sessions,
      total_count: sessionsData.sessions.length,
      active_count: sessionsData.sessions.filter(s => s.is_active).length
    };
  }

  static async createSession(
    request: SessionCreateRequest
  ): Promise<SessionInfo> {
    // For now, we'll create a session by connecting to WebSocket
    // The actual session creation happens on the backend when WebSocket connects
    const token = this.getStoredToken();
    if (!token) {
      throw new SessionAPIError("No authentication token found");
    }

    // Connect to WebSocket to create a session
    const connected = await this.connectWebSocket(token);
    if (!connected) {
      throw new SessionAPIError("Failed to create session - WebSocket connection failed");
    }

    // Return a mock session object that will be updated when session_ready is received
    return {
      session_id: "pending-session-id",
      user_id: request.user_id,
      created_at: new Date().toISOString(),
      last_activity: new Date().toISOString(),
      is_active: true,
      graph_data: {},
      chat_history: []
    };
  }

  static async destroySession(_sessionId: string): Promise<{ message: string }> {
    // For WebSocket-based sessions, we close the WebSocket connection
    this.disconnectWebSocket();
    return { message: "Session destroyed" };
  }

  // Helper methods for session data processing
  private static determineSessionStatus(session: Record<string, unknown>): string {
    if (!session.is_active) {
      return "expired";
    }
    
    const now = new Date();
    const lastActivity = new Date(session.last_activity as string);
    const timeDiff = now.getTime() - lastActivity.getTime();
    const minutesDiff = timeDiff / (1000 * 60);
    
    if (minutesDiff < 5) {
      return "active";
    } else if (minutesDiff < 30) {
      return "paused";
    } else {
      return "expired";
    }
  }

  private static extractAgentCount(session: Record<string, unknown>): number {
    // Extract agent count from graph_data or default to 0
    if (session.graph_data && typeof session.graph_data === 'object') {
      return (session.graph_data as Record<string, unknown>).agent_count as number || 0;
    }
    return 0;
  }

  private static extractTaskCount(session: Record<string, unknown>): number {
    // Extract task count from graph_data or default to 0
    if (session.graph_data && typeof session.graph_data === 'object') {
      return (session.graph_data as Record<string, unknown>).task_count as number || 0;
    }
    return 0;
  }

  static getStoredToken(): string | null {
    // Get token from localStorage or sessionStorage
    const token = localStorage.getItem('authToken') || sessionStorage.getItem('authToken');
    
    if (!token) {
      return null;
    }
    
    // Check if token is expired
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      const now = Math.floor(Date.now() / 1000);
      
      if (payload.exp && payload.exp < now) {
        this.clearStoredToken();
        return null;
      }
      
      return token;
    } catch {
      // If token is malformed, clear it
      this.clearStoredToken();
      return null;
    }
  }

  static clearStoredToken(): void {
    localStorage.removeItem('authToken');
    localStorage.removeItem('authUser');
    sessionStorage.removeItem('authToken');
    sessionStorage.removeItem('authUser');
  }

  static async refreshToken(): Promise<string> {
    const loginResult = await this.login("testuser", "testpass");
    this.clearStoredToken();
    localStorage.setItem('authToken', loginResult.access_token);
    localStorage.setItem('authUser', loginResult.user_id);
    return loginResult.access_token;
  }

  // Task management functions
  static async getTasks(_sessionId: string): Promise<{ tasks: TaskInfo[] }> {
    // This would require authentication headers in a real implementation
    // For now, return empty tasks array
    return { tasks: [] };
  }

  static async addTask(sessionId: string, task: Omit<TaskInfo, 'id' | 'created_at'>): Promise<TaskInfo> {
    // This would require authentication headers in a real implementation
    // For now, create a mock task
    const newTask: TaskInfo = {
      id: `task-${Date.now()}`,
      created_at: new Date().toISOString(),
      ...task
    };
    return newTask;
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
      // Check if we already have a valid token
      let token = SessionAPI.getStoredToken();
      
      if (!token) {
        // If no token, try to login with default credentials
        const loginResult = await SessionAPI.login("testuser", "testpass");
        token = loginResult.access_token;
        
        // Store token for future use
        localStorage.setItem('authToken', token);
        localStorage.setItem('authUser', loginResult.user_id);
      }
      const connected = await SessionAPI.connectWebSocket(token);
      
      if (!connected) {
        throw new SessionAPIError("Failed to connect to WebSocket");
      }
      
      setIsConnected(true);
      
      // Create a session object for the frontend
      const session: SessionInfo = {
        session_id: SessionAPI.getSessionId() || "unknown",
        user_id: request.user_id,
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
      
      // Clear stored authentication data
      localStorage.removeItem('authToken');
      localStorage.removeItem('authUser');
      sessionStorage.removeItem('authToken');
      sessionStorage.removeItem('authUser');
      
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

// State update hook for converting state_update messages to task updates
export function useStateUpdates(sessionId: string | null) {
  const [stateUpdates, setStateUpdates] = useState<StateUpdateData[]>([]);
  const [error, setError] = useState<SessionAPIError | null>(null);

  // Add message listener on component mount
  useEffect(() => {
    if (!sessionId) return;

    const handleMessage = (message: Message) => {
      if (message.type === "state_update" && message.data) {
        try {
          const stateUpdateData = message.data as unknown as StateUpdateData;
          setStateUpdates(prev => [...prev, stateUpdateData]);
        } catch (err) {
          // eslint-disable-next-line no-console
          console.error("Error parsing state update message:", err);
          setError(new SessionAPIError("Failed to parse state update message"));
        }
      }
    };

    SessionAPI.addMessageListener(handleMessage);
    
    // Cleanup listener on unmount
    return () => {
      SessionAPI.removeMessageListener(handleMessage);
    };
  }, [sessionId]);

  // Convert state updates to task updates
  const convertToTaskUpdates = useCallback((stateUpdate: StateUpdateData): TaskInfo[] => {
    const tasks: TaskInfo[] = [];
    
    // Convert todo items to tasks
    stateUpdate.todo_list.forEach((todo, index) => {
      const task: TaskInfo = {
        id: `todo-${stateUpdate.update_type}-${index}`,
        title: todo.description,
        description: `Tool: ${todo.tool_name || 'unknown'}, Complexity: ${todo.estimated_complexity || 'medium'}`,
        status: todo.status === "done" ? "completed" : "pending",
        priority: todo.estimated_complexity === "high" ? "high" : 
                 todo.estimated_complexity === "low" ? "low" : "medium",
        created_at: new Date().toISOString(),
        metadata: {
          step_number: todo.step_number,
          tool_name: todo.tool_name,
          update_type: stateUpdate.update_type,
          current_step: stateUpdate.current_step
        }
      };
      tasks.push(task);
    });

    // Convert entities to tasks if they represent actionable items
    stateUpdate.entities_created.forEach((entity, index) => {
      if (entity.type === "node" && entity.label) {
        const task: TaskInfo = {
          id: `entity-${stateUpdate.update_type}-${index}`,
          title: `Create ${entity.label}: ${entity.name}`,
          description: `Entity type: ${entity.type}, Properties: ${JSON.stringify(entity.properties)}`,
          status: "completed", // Entities that are created are considered completed
          priority: "medium",
          created_at: new Date().toISOString(),
          metadata: {
            entity_name: entity.name,
            entity_type: entity.type,
            entity_label: entity.label,
            confidence: entity.confidence,
            update_type: stateUpdate.update_type
          }
        };
        tasks.push(task);
      }
    });

    return tasks;
  }, []);

  const clearStateUpdates = useCallback(() => {
    setStateUpdates([]);
  }, []);

  return {
    stateUpdates,
    error,
    convertToTaskUpdates,
    clearStateUpdates,
  };
}

// Log configuration on module load
if (config.isDebugMode()) {
  config.logConfiguration();
}


