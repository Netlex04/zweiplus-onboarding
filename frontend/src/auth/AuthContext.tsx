/**
 * Authentication state: token + role + name held in memory and mirrored to
 * localStorage so a reload restores the session. The in-memory token is also
 * pushed into the API http layer for Bearer injection.
 */

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { login as loginRequest, setAuthToken } from "../api";
import type { Role } from "../api";

const STORAGE_KEY = "zweiplus.auth";

export interface AuthUser {
  token: string;
  role: Role;
  name: string;
}

interface AuthContextValue {
  user: AuthUser | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<AuthUser>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function readStored(): AuthUser | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as AuthUser;
    if (parsed && parsed.token && parsed.role && parsed.name) return parsed;
  } catch {
    // ignore malformed storage
  }
  return null;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(() => {
    const stored = readStored();
    if (stored) setAuthToken(stored.token);
    return stored;
  });

  // Keep the http layer's token in sync with state.
  useEffect(() => {
    setAuthToken(user?.token ?? null);
  }, [user]);

  const login = useCallback(async (email: string, password: string): Promise<AuthUser> => {
    const res = await loginRequest({ email, password });
    const next: AuthUser = { token: res.token, role: res.role, name: res.name };
    setAuthToken(next.token);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
    setUser(next);
    return next;
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY);
    setAuthToken(null);
    setUser(null);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({ user, isAuthenticated: user !== null, login, logout }),
    [user, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
