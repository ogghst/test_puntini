import { createContext, useContext, useState, useEffect, type ReactNode } from "react";
import { SessionAPI } from "@/utils/session";

// Base API configuration
const API_BASE_URL = "http://localhost:8009";

interface AuthContextType {
  user: { username: string; email: string; full_name: string } | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, password: string) => Promise<void>;
  logout: () => void;
  loading: boolean;
  error: string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<{ username: string; email: string; full_name: string } | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Check if user is already logged in on initial load
  useEffect(() => {
    const storedToken = localStorage.getItem("authToken");
    const storedUser = localStorage.getItem("authUser");
    
    if (storedToken && storedUser) {
      setToken(storedToken);
      setUser(JSON.parse(storedUser));
    }
  }, []);

  const login = async (username: string, password: string) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await SessionAPI.login(username, password);
      setToken(result.access_token);
      
      // Get user info from the /me endpoint
      const userResponse = await fetch(`${API_BASE_URL}/me`, {
        headers: {
          "Authorization": `Bearer ${result.access_token}`
        }
      });
      
      if (userResponse.ok) {
        const userObj = await userResponse.json();
        setUser(userObj);
        
        // Store in localStorage
        localStorage.setItem("authToken", result.access_token);
        localStorage.setItem("authUser", JSON.stringify(userObj));
      } else {
        // Fallback to mock user if /me fails
        const userObj = {
          username: result.user_id,
          email: `${result.user_id}@example.com`,
          full_name: result.user_id.charAt(0).toUpperCase() + result.user_id.slice(1)
        };
        setUser(userObj);
        
        // Store in localStorage
        localStorage.setItem("authToken", result.access_token);
        localStorage.setItem("authUser", JSON.stringify(userObj));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const register = async (username: string, password: string) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await SessionAPI.register(username, password);
      setUser(result);
      
      // Store in localStorage
      localStorage.setItem("authUser", JSON.stringify(result));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem("authToken");
    localStorage.removeItem("authUser");
    SessionAPI.disconnectWebSocket();
  };

  const value = {
    user,
    token,
    isAuthenticated: !!user,
    login,
    register,
    logout,
    loading,
    error
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}