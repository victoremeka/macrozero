// API configuration
const API_BASE_URL = 'http://localhost:8000';

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
  initiateLogin(): void {
    window.location.href = `${this.baseUrl}/auth/login`;
  }

  /**
   * Get current authenticated user
   */
  async getCurrentUser(): Promise<User | null> {
    try {
      const response = await fetch(`${this.baseUrl}/auth/me`, {
        credentials: 'include', // Include HTTP-only cookies
      });

      if (response.ok) {
        const user = await response.json();
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
      const response = await fetch(`${this.baseUrl}/auth/logout`, {
        method: 'POST',
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error(`Logout failed: ${response.status}`);
      }
    } catch (error) {
      console.error('Logout failed:', error);
      throw error;
    }
  }

  /**
   * Make authenticated API request
   */
  async authenticatedRequest(endpoint: string, options: RequestInit = {}): Promise<Response> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      credentials: 'include', // Include HTTP-only cookies
    });

    if (response.status === 401) {
      // Redirect to login if unauthorized
      this.initiateLogin();
      throw new Error('Unauthorized - redirecting to login');
    }

    return response;
  }
}

// Export singleton instance
export const authAPI = new AuthAPI();

// Utility functions
export const redirectToLogin = () => authAPI.initiateLogin();
export const getCurrentUser = () => authAPI.getCurrentUser();
export const logout = () => authAPI.logout();
export const makeAuthenticatedRequest = (endpoint: string, options?: RequestInit) => 
  authAPI.authenticatedRequest(endpoint, options);