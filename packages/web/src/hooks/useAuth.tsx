import { createContext, useContext, useState, useEffect } from "react";
import type { ReactNode } from "react";
import type { User, AuthResponse } from "../types";
import { authApi } from "../api/auth";
import type {
  SignInRequest,
  SignUpRequest,
  TelegramAuthData,
} from "../api/auth";

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  signIn: (data: SignInRequest) => Promise<void>;
  signUp: (data: SignUpRequest) => Promise<void>;
  telegramSignIn: (data: TelegramAuthData) => Promise<void>;
  signOut: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Load user and token from localStorage on mount
    const storedToken = localStorage.getItem("access_token");
    const storedUser = localStorage.getItem("user");

    if (storedToken && storedUser) {
      setToken(storedToken);
      setUser(JSON.parse(storedUser));
    }
    setIsLoading(false);
  }, []);

  const signIn = async (data: SignInRequest) => {
    const response: AuthResponse = await authApi.signIn(data);
    setToken(response.access_token);
    setUser(response.user);
    localStorage.setItem("access_token", response.access_token);
    localStorage.setItem("user", JSON.stringify(response.user));
  };

  const signUp = async (data: SignUpRequest) => {
    const response: AuthResponse = await authApi.signUp(data);
    setToken(response.access_token);
    setUser(response.user);
    localStorage.setItem("access_token", response.access_token);
    localStorage.setItem("user", JSON.stringify(response.user));
  };

  const telegramSignIn = async (data: TelegramAuthData) => {
    const response = await authApi.telegramAuth(data);
    setToken(response.access_token);
    setUser(response.user);
    localStorage.setItem("access_token", response.access_token);
    localStorage.setItem("user", JSON.stringify(response.user));
  };

  const signOut = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!token,
        isLoading,
        signIn,
        signUp,
        telegramSignIn,
        signOut,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
