import { createContext, useContext, useEffect, useState } from "react";
import { api, clearAuthToken, getAuthToken, setAuthToken } from "./api";
import type { User } from "./types";

type AuthContextValue = {
  token: string | null;
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, displayName: string) => Promise<void>;
  logout: () => void;
  acceptToken: (token: string) => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(() => getAuthToken());
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(Boolean(token));

  useEffect(() => {
    const onUnauthorized = () => {
      setToken(null);
      setUser(null);
      setLoading(false);
    };
    window.addEventListener("auth:unauthorized", onUnauthorized);
    return () => window.removeEventListener("auth:unauthorized", onUnauthorized);
  }, []);

  useEffect(() => {
    if (!token) {
      setLoading(false);
      return;
    }
    setLoading(true);
    api.me()
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setLoading(false));
  }, [token]);

  function saveAuth(nextToken: string, nextUser?: User) {
    setAuthToken(nextToken);
    setToken(nextToken);
    if (nextUser) setUser(nextUser);
  }

  async function login(email: string, password: string) {
    const result = await api.login(email, password);
    saveAuth(result.access_token, result.user);
  }

  async function signup(email: string, password: string, displayName: string) {
    const result = await api.signup(email, password, displayName);
    saveAuth(result.access_token, result.user);
  }

  function logout() {
    clearAuthToken();
    setToken(null);
    setUser(null);
  }

  async function acceptToken(nextToken: string) {
    saveAuth(nextToken);
    setLoading(true);
    try {
      setUser(await api.me());
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthContext.Provider value={{ token, user, loading, login, signup, logout, acceptToken }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}
