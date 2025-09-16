import api, { API_BASE_URL, getErrorMessage, isAxiosError } from './api';

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

export interface LoginResponse {
  url: string;
}

class AuthAPI {
  /**
   * Redirect to GitHub OAuth login
   */
  async initiateLogin(): Promise<void> {
    try {
      const response = await api.get<LoginResponse>('/auth/login');
      const data = response.data;
      
      if (!data.url) {
        throw new Error('No login URL received from server');
      }
      
      window.location.href = data.url;
    } catch (error) {
      console.error('Failed to initiate login:', getErrorMessage(error));
      throw new Error('Failed to start login process. Please try again.');
    }
  }

  /**
   * Get current authenticated user
   */
  async getCurrentUser(): Promise<User | null> {
    try {
      const response = await api.get<User>('/auth/me');
      
      if (response.status === 200) {
        return response.data;
      }
      
      return null;
    } catch (error) {
      if (isAxiosError(error) && error.response?.status === 401) {
        // User is not authenticated - this is expected
        return null;
      }
      
      console.error('Auth check failed:', getErrorMessage(error));
      return null;
    }
  }

  /**
   * Logout current user
   */
  async logout(): Promise<void> {
    try {
      const response = await api.post<AuthResponse>('/auth/logout');
      
      if (response.status !== 200) {
        throw new Error(`Logout failed with status: ${response.status}`);
      }
    } catch (error) {
      console.error('Logout failed:', getErrorMessage(error));
      throw new Error('Failed to logout. Please try again.');
    }
  }

  /**
   * Handle OAuth callback after GitHub redirect
   */
  async handleCallback(code: string, state: string): Promise<void> {
    try {
      const response = await api.post<AuthResponse>('/auth/callback', {
        code,
        state,
      });
      
      if (response.status !== 200) {
        throw new Error(`Callback failed with status: ${response.status}`);
      }
    } catch (error) {
      console.error('OAuth callback failed:', getErrorMessage(error));
      throw new Error('Authentication failed. Please try again.');
    }
  }
}

// Export singleton instance
export const authAPI = new AuthAPI();

// Utility functions
export const redirectToLogin = () => authAPI.initiateLogin();
export const getCurrentUser = () => authAPI.getCurrentUser();
export const logout = () => authAPI.logout();
export const handleAuthCallback = (code: string, state: string) => 
  authAPI.handleCallback(code, state);

// Export API_BASE_URL for backward compatibility
export { API_BASE_URL };