/**
 * Session management service for the business improvement project management system.
 *
 * This module provides TypeScript interfaces and API functions that are compliant
 * with the backend session management system.
 */

// Base API configuration
const API_BASE_URL = "http://localhost:8001";

// Session-related types (compliant with backend models)
export interface SessionInfo {
  session_id: string;
  user_id: string;
  project_id?: string;
  status: SessionStatus;
  created_at: string;
  last_activity: string;
  expires_at: string;
  is_expired: boolean;
  is_active: boolean;
  agent_count: number;
  task_count: number;
  metadata: Record<string, any>;
}

export type SessionStatus =
  | "initializing"
  | "active"
  | "paused"
  | "expired"
  | "error"
  | "cleaning_up";

export interface Message {
  id: string;
  content: any;
  timestamp: string;
  message_type: MessageType;
  metadata: Record<string, any>;
}

export type MessageType = "user" | "system" | "agent" | "error";

export interface SessionCreateRequest {
  user_id: string;
  project_id?: string;
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
    public status?: number,
    public details?: any
  ) {
    super(message);
    this.name = "SessionAPIError";
  }
}

// Session API functions
export class SessionAPI {
  private static async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;

    const defaultHeaders = {
      "Content-Type": "application/json",
    };

    const response = await fetch(url, {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers,
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

    return response.json();
  }

  // Session management
  static async createSession(
    request: SessionCreateRequest
  ): Promise<SessionInfo> {
    return this.request<SessionInfo>("/sessions", {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  static async getSession(sessionId: string): Promise<SessionInfo> {
    return this.request<SessionInfo>(`/sessions/${sessionId}`);
  }

  static async destroySession(sessionId: string): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/sessions/${sessionId}`, {
      method: "DELETE",
    });
  }

  static async listSessions(userId?: string): Promise<SessionListResponse> {
    const params = userId ? `?user_id=${encodeURIComponent(userId)}` : "";
    return this.request<SessionListResponse>(`/sessions${params}`);
  }

  static async getSessionStats(): Promise<SessionStats> {
    return this.request<SessionStats>("/sessions/stats");
  }

  // Message management
  static async sendMessage(
    sessionId: string,
    request: MessageRequest
  ): Promise<Message> {
    return this.request<Message>(`/sessions/${sessionId}/messages`, {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  static async receiveMessage(
    sessionId: string,
    timeout?: number
  ): Promise<Message | { message: string; timeout: boolean }> {
    const params = timeout ? `?timeout=${timeout}` : "";
    return this.request<Message | { message: string; timeout: boolean }>(
      `/sessions/${sessionId}/messages${params}`
    );
  }

  // Project context management
  static async getProjectContext(sessionId: string): Promise<ProjectContext> {
    return this.request<ProjectContext>(`/sessions/${sessionId}/context`);
  }

  static async updateProjectContext(
    sessionId: string,
    context: Record<string, any>
  ): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/sessions/${sessionId}/context`, {
      method: "PUT",
      body: JSON.stringify(context),
    });
  }

  // Task management
  static async addTask(
    sessionId: string,
    task: Omit<TaskInfo, "id" | "created_at">
  ): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/sessions/${sessionId}/tasks`, {
      method: "POST",
      body: JSON.stringify(task),
    });
  }

  static async getTasks(
    sessionId: string
  ): Promise<{ tasks: TaskInfo[]; count: number }> {
    return this.request<{ tasks: TaskInfo[]; count: number }>(
      `/sessions/${sessionId}/tasks`
    );
  }
}

// Session management hook for React components
export function useSession() {
  const [currentSession, setCurrentSession] = useState<SessionInfo | null>(
    null
  );
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<SessionAPIError | null>(null);

  const createSession = useCallback(async (request: SessionCreateRequest) => {
    setIsLoading(true);
    setError(null);

    try {
      const session = await SessionAPI.createSession(request);
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
    if (!currentSession) return;

    setIsLoading(true);
    setError(null);

    try {
      await SessionAPI.destroySession(currentSession.session_id);
      setCurrentSession(null);
    } catch (err) {
      const apiError =
        err instanceof SessionAPIError
          ? err
          : new SessionAPIError("Failed to destroy session");
      setError(apiError);
      throw apiError;
    } finally {
      setIsLoading(false);
    }
  }, [currentSession]);

  const refreshSession = useCallback(async () => {
    if (!currentSession) return;

    setIsLoading(true);
    setError(null);

    try {
      const session = await SessionAPI.getSession(currentSession.session_id);
      setCurrentSession(session);
    } catch (err) {
      const apiError =
        err instanceof SessionAPIError
          ? err
          : new SessionAPIError("Failed to refresh session");
      setError(apiError);
      throw apiError;
    } finally {
      setIsLoading(false);
    }
  }, [currentSession]);

  return {
    currentSession,
    isLoading,
    error,
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

  const sendMessage = useCallback(
    async (request: MessageRequest) => {
      if (!sessionId) throw new Error("No session available");

      setIsLoading(true);
      setError(null);

      try {
        const message = await SessionAPI.sendMessage(sessionId, request);
        setMessages((prev) => [...prev, message]);
        return message;
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
    [sessionId]
  );

  const receiveMessage = useCallback(
    async (timeout?: number) => {
      if (!sessionId) throw new Error("No session available");

      setIsLoading(true);
      setError(null);

      try {
        const result = await SessionAPI.receiveMessage(sessionId, timeout);

        if ("timeout" in result && result.timeout) {
          return null;
        }

        const message = result as Message;
        setMessages((prev) => [...prev, message]);
        return message;
      } catch (err) {
        const apiError =
          err instanceof SessionAPIError
            ? err
            : new SessionAPIError("Failed to receive message");
        setError(apiError);
        throw apiError;
      } finally {
        setIsLoading(false);
      }
    },
    [sessionId]
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

// Import React for hooks
import { useCallback, useState } from "react";
