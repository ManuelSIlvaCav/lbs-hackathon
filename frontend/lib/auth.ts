/**
 * Authentication utilities for token management and error handling
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface AuthTokens {
  accessToken: string | null;
  refreshToken: string | null;
}

export interface User {
  id: string;
  email: string;
  full_name?: string;
  role: string;
  candidate_id?: string;
}

/**
 * Get stored access token
 */
export const getAccessToken = (): string | null => {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token");
};

/**
 * Get stored refresh token
 */
export const getRefreshToken = (): string | null => {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("refresh_token");
};

/**
 * Store authentication tokens
 */
export const setTokens = (accessToken: string, refreshToken: string): void => {
  if (typeof window === "undefined") return;
  localStorage.setItem("access_token", accessToken);
  localStorage.setItem("refresh_token", refreshToken);
};

/**
 * Clear all authentication tokens and user data
 */
export const clearAuth = (): void => {
  if (typeof window === "undefined") return;
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  localStorage.removeItem("user");
};

/**
 * Get stored user data
 */
export const getUser = (): User | null => {
  if (typeof window === "undefined") return null;
  const userStr = localStorage.getItem("auth_user");
  if (!userStr) return null;
  try {
    return JSON.parse(userStr);
  } catch {
    return null;
  }
};

/**
 * Store user data
 */
export const setUser = (user: User): void => {
  if (typeof window === "undefined") return;
  localStorage.setItem("user", JSON.stringify(user));
};

/**
 * Refresh the access token using the refresh token
 */
export const refreshAccessToken = async (): Promise<boolean> => {
  const refreshToken = getRefreshToken();
  
  if (!refreshToken) {
    console.error("No refresh token available");
    return false;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/auth/refresh`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ token: refreshToken }),
    });

    if (!response.ok) {
      console.error("Failed to refresh token");
      return false;
    }

    const data = await response.json();
    
    // Store new tokens
    setTokens(data.access_token, data.refresh_token);
    
    // Update user data (in case candidate_id was added)
    if (data.user) {
      setUser(data.user);
    }

    return true;
  } catch (error) {
    console.error("Error refreshing token:", error);
    return false;
  }
};

/**
 * Force logout - clear tokens and redirect to login
 */
export const forceLogout = (): void => {
  clearAuth();
  if (typeof window !== "undefined") {
    window.location.href = "/login";
  }
};

/**
 * Handle authentication errors with configurable strategy
 */
export interface AuthErrorHandlerOptions {
  /**
   * Strategy to use when authentication fails
   * - "refresh": Try to refresh the token first, logout if refresh fails
   * - "logout": Immediately logout without attempting refresh
   */
  strategy?: "refresh" | "logout";
  
  /**
   * Custom error handler
   */
  onError?: (error: Error) => void;
}

/**
 * Handle authentication errors (401 Unauthorized)
 * 
 * @param error - The error to handle
 * @param options - Configuration options
 * @returns Promise that resolves to true if token was refreshed, false otherwise
 */
export const handleAuthError = async (
  error: any,
  options: AuthErrorHandlerOptions = {}
): Promise<boolean> => {
  const { strategy = "refresh", onError } = options;

  // Check if it's a 401 Unauthorized error
  const is401 = 
    error?.response?.status === 401 || 
    error?.message?.includes("401") ||
    error?.message?.includes("Unauthorized");

  if (!is401) {
    // Not an auth error, let it propagate
    if (onError) onError(error);
    throw error;
  }

  // Handle based on strategy
  if (strategy === "logout") {
    console.log("Authentication failed - forcing logout");
    forceLogout();
    return false;
  }

  // Default: try to refresh token
  console.log("Authentication failed - attempting token refresh");
  const refreshed = await refreshAccessToken();

  if (refreshed) {
    console.log("Token refreshed successfully");
    return true;
  }

  // Refresh failed, force logout
  console.log("Token refresh failed - forcing logout");
  forceLogout();
  return false;
};

/**
 * Make an authenticated API request with automatic token refresh
 * 
 * @param url - API endpoint URL
 * @param options - Fetch options
 * @param authOptions - Authentication error handling options
 * @returns Promise with the response
 */
export const authenticatedFetch = async (
  url: string,
  options: RequestInit = {},
  authOptions: AuthErrorHandlerOptions = {}
): Promise<Response> => {
  const accessToken = getAccessToken();

  if (!accessToken) {
    throw new Error("No access token available");
  }

  // Add authorization header
  const headers = {
    ...options.headers,
    Authorization: `Bearer ${accessToken}`,
  };

  try {
    const response = await fetch(url, { ...options, headers });

    // If 401, handle auth error
    if (response.status === 401) {
      const refreshed = await handleAuthError(
        { response },
        authOptions
      );

      // If token was refreshed, retry the request
      if (refreshed) {
        const newToken = getAccessToken();
        const retryHeaders = {
          ...options.headers,
          Authorization: `Bearer ${newToken}`,
        };
        return fetch(url, { ...options, headers: retryHeaders });
      }
    }

    return response;
  } catch (error) {
    await handleAuthError(error, authOptions);
    throw error;
  }
};

/**
 * Utility to create fetch options with JWT authentication
 */
export const createAuthHeaders = (jwt?: string): HeadersInit => {
  const token = jwt || getAccessToken();
  
  if (!token) {
    throw new Error("No authentication token available");
  }

  return {
    Authorization: `Bearer ${token}`,
  };
};
