import { type ReactNode, useContext } from "react";
import { AuthContext } from "./AuthContext";
import { LoginPage } from "./LoginPage";

interface ProtectedRouteProps {
  children: ReactNode;
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const authContext = useContext(AuthContext);
  
  // Handle case where AuthProvider is not available
  if (!authContext) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Loading...</h1>
          <p className="text-gray-600">Initializing authentication...</p>
        </div>
      </div>
    );
  }

  const { isAuthenticated, loading } = authContext;

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginPage />;
  }

  return <>{children}</>;
}