import axios from "axios";

// API configuration
export const API_BASE_URL = process.env.API_BASE_URL!;

export interface User {
  github_id: number;
  username: string;
  name: string | null;
  email: string | null;
  avatar_url: string;
}

export interface AuthResponse {
  message: string;
}

class AuthAPI {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  /**
   * Redirect to GitHub OAuth login
   */
  async initiateLogin(): Promise<void> {
    const response = await axios.get(`${API_BASE_URL}/auth/login`);
    const data = response.data;
    window.location.href = data.url;
  }

  /**
   * Get current authenticated user
   */
  async getCurrentUser(): Promise<User | null> {
    try {
      const response = await axios.get(`${this.baseUrl}/auth/me`, {
        withCredentials: true, // Include HTTP-only cookies
      });

      if (response.status === 200) {
        const user = response.data;
        return user;
      } else if (response.status === 401) {
        return null; // Not authenticated
      } else {
        throw new Error(`Failed to get user: ${response.status}`);
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      return null;
    }
  }

  /**
   * Logout current user
   */
  async logout(): Promise<void> {
    try {
      const response = await axios.post(`${this.baseUrl}/auth/logout`, {
        withCredentials: true,
      });

      if (response.status !== 200) {
        throw new Error(`Logout failed: ${response.status}`);
      }
    } catch (error) {
      console.error('Logout failed:', error);
      throw error;
    }
  }
}

// Export singleton instance
export const authAPI = new AuthAPI();

// Utility functions
export const redirectToLogin = () => authAPI.initiateLogin();
export const getCurrentUser = () => authAPI.getCurrentUser();
export const logout = () => authAPI.logout();