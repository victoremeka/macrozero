import axios, { type AxiosInstance, type AxiosError } from 'axios';

// Get API base URL from environment variables with fallback
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Create axios instance with default configuration
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds timeout
  withCredentials: true, // Include cookies in all requests
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for adding auth headers or other global configs
api.interceptors.request.use(
  (config) => {
    // Log request in development
    if (import.meta.env.DEV) {
      console.log(`Making ${config.method?.toUpperCase()} request to ${config.url}`);
    }
    return config;
  },
  (error) => {
    console.error('Request interceptor error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for global error handling
api.interceptors.response.use(
  (response) => {
    // Log successful responses in development
    if (import.meta.env.DEV) {
      console.log(`Response from ${response.config.url}:`, response.status);
    }
    return response;
  },
  (error: AxiosError) => {
    // Handle common error scenarios
    if (error.response) {
      const { status, data } = error.response;
      
      switch (status) {
        case 401:
          console.warn('Unauthorized request - user may need to log in');
          // Don't redirect automatically - let components handle this
          break;
        case 403:
          console.error('Forbidden - insufficient permissions');
          break;
        case 404:
          console.error('Resource not found');
          break;
        case 429:
          console.error('Rate limited - too many requests');
          break;
        case 500:
          console.error('Server error - please try again later');
          break;
        default:
          console.error(`Request failed with status ${status}:`, data);
      }
    } else if (error.request) {
      console.error('Network error - no response received:', error.message);
    } else {
      console.error('Request setup error:', error.message);
    }

    return Promise.reject(error);
  }
);

// Export the configured axios instance
export default api;

// Export the base URL for use in other files
export { API_BASE_URL };

// Helper function to check if error is an axios error
export const isAxiosError = (error: unknown): error is AxiosError => {
  return axios.isAxiosError(error);
};

// Helper function to extract error message from axios error
export const getErrorMessage = (error: unknown): string => {
  if (isAxiosError(error)) {
    if (error.response?.data && typeof error.response.data === 'object') {
      const data = error.response.data as Record<string, unknown>;
      if (typeof data.detail === 'string') {
        return data.detail;
      }
      if (typeof data.message === 'string') {
        return data.message;
      }
    }
    if (error.response?.statusText) {
      return error.response.statusText;
    }
    if (error.message) {
      return error.message;
    }
  }
  
  if (error instanceof Error) {
    return error.message;
  }
  
  return 'An unexpected error occurred';
};