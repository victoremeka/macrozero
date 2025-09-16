import { useState, useEffect } from "react";
import type { ReactNode } from "react";
import type { User } from "@/lib/auth";
import {
  getCurrentUser,
  logout as logoutAPI,
  redirectToLogin,
  handleAuthCallback,
} from "@/lib/auth";
import { AuthContext, type AuthContextType } from "./auth-context";

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const isAuthenticated = !!user;

  const clearError = () => {
    setError(null);
  };

  const refreshUser = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const currentUser = await getCurrentUser();
      setUser(currentUser);
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to refresh user";
      console.error("Failed to refresh user:", errorMessage);
      setError(errorMessage);
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  const login = async () => {
    try {
      setError(null);
      setIsLoading(true);
      await redirectToLogin();
      // Note: The actual login happens on GitHub's site and redirects back
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to start login";
      console.error("Login failed:", errorMessage);
      setError(errorMessage);
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      setError(null);
      setIsLoading(true);
      await logoutAPI();
      setUser(null);
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to logout";
      console.error("Logout failed:", errorMessage);
      setError(errorMessage);
      // Clear user state even if logout fails
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCallback = async (code: string) => {
    try {
      setError(null);
      setIsLoading(true);
      await handleAuthCallback(code);
      // After successful callback, refresh user data
      await refreshUser();
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Authentication failed";
      console.error("OAuth callback failed:", errorMessage);
      setError(errorMessage);
      setUser(null);
      setIsLoading(false);
    }
  };

  // Check authentication status on mount
  useEffect(() => {
    refreshUser();
  }, []);

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated,
    error,
    login,
    logout,
    refreshUser,
    handleCallback,
    clearError,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
