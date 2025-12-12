"use client";

import {
  createContext,
  ReactNode,
  useContext,
  useEffect,
  useState,
} from "react";

interface User {
  id: string;
  email: string;
  full_name?: string;
  role: "user" | "admin";
  is_active: boolean;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (email: string, password: string, isAdmin?: boolean) => Promise<void>;
  signup: (email: string, password: string, fullName?: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
  isAdmin: boolean;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Load token from localStorage on mount
  useEffect(() => {
    const storedToken = localStorage.getItem("access_token");
    const storedUser = localStorage.getItem("auth_user");

    if (storedToken && storedUser) {
      setToken(storedToken);
      setUser(JSON.parse(storedUser));
    }
    setIsLoading(false);
  }, []);

  const signup = async (email: string, password: string, fullName?: string) => {
    const response = await fetch("http://localhost:8000/api/auth/signup", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        email,
        password,
        full_name: fullName,
        role: "user",
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Signup failed");
    }

    const data = await response.json();

    // Store token and user
    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("auth_user", JSON.stringify(data.user));

    setToken(data.access_token);
    setUser(data.user);
  };

  const login = async (
    email: string,
    password: string,
    isAdmin: boolean = false
  ) => {
    const endpoint = isAdmin
      ? "http://localhost:8000/api/auth/admin/login"
      : "http://localhost:8000/api/auth/login";

    const response = await fetch(endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Login failed");
    }

    const data = await response.json();

    // Store token and user
    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("auth_user", JSON.stringify(data.user));

    setToken(data.access_token);
    setUser(data.user);
  };

  const logout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("auth_user");
    setToken(null);
    setUser(null);
  };

  const value = {
    user,
    token,
    login,
    signup,
    logout,
    isAuthenticated: !!token && !!user,
    isAdmin: user?.role === "admin",
    isLoading,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
