import { createContext, useContext, useState, useCallback, type ReactNode } from "react";
import { login as apiLogin, setToken } from "../lib/api";

interface User {
  id: string;
  email: string;
  role: string;
  name: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(() => {
    const stored = sessionStorage.getItem("user");
    const token = sessionStorage.getItem("token");
    if (stored && token) {
      setToken(token);
      return JSON.parse(stored);
    }
    return null;
  });

  const login = useCallback(async (email: string, password: string) => {
    const response = await apiLogin(email, password);
    setToken(response.access_token);
    sessionStorage.setItem("token", response.access_token);

    // Decode JWT payload to get user info
    const payload = JSON.parse(atob(response.access_token.split(".")[1]));
    const userData: User = {
      id: payload.sub,
      email: payload.email,
      role: payload.role,
      name: payload.name,
    };
    setUser(userData);
    sessionStorage.setItem("user", JSON.stringify(userData));
  }, []);

  const logout = useCallback(() => {
    setUser(null);
    setToken(null);
    sessionStorage.removeItem("token");
    sessionStorage.removeItem("user");
  }, []);

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider");
  return context;
}
