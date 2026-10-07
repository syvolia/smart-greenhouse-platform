import {
  createContext,
  useContext,
  useCallback,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { api, tokenStore } from "../api/client";
import type { User, UserRole } from "../api/types";

interface AuthState {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  hasRole: (roles: UserRole[]) => boolean;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const loadMe = useCallback(async () => {
    try {
      const me = await api.me();
      setUser(me);
    } catch {
      tokenStore.clear();
      setUser(null);
    }
  }, []);

  // On mount, try to refresh and load /me
  useEffect(() => {
    (async () => {
      const refresh = tokenStore.getRefresh();
      if (!refresh) {
        setLoading(false);
        return;
      }
      try {
        const res = await fetch(
          `${import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8002"}/auth/refresh`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ refresh_token: refresh }),
          }
        );
        if (res.ok) {
          const pair = await res.json();
          tokenStore.setAccess(pair.access_token);
          tokenStore.setRefresh(pair.refresh_token);
          await loadMe();
        } else {
          tokenStore.clear();
        }
      } catch {
        tokenStore.clear();
      } finally {
        setLoading(false);
      }
    })();
  }, [loadMe]);

  // Wire the client's 401 handler to clear auth state
  useEffect(() => {
    tokenStore.onUnauthorized(() => {
      setUser(null);
    });
    return () => tokenStore.onUnauthorized(null);
  }, []);

  const login = useCallback(
    async (email: string, password: string) => {
      const pair = await api.login(email, password);
      tokenStore.setAccess(pair.access_token);
      tokenStore.setRefresh(pair.refresh_token);
      await loadMe();
    },
    [loadMe]
  );

  const logout = useCallback(async () => {
    const refresh = tokenStore.getRefresh();
    try {
      if (refresh) await api.logout(refresh);
    } catch {
      /* best-effort */
    }
    tokenStore.clear();
    setUser(null);
  }, []);

  const hasRole = useCallback(
    (roles: UserRole[]) => {
      if (!user) return false;
      return roles.includes(user.role);
    },
    [user]
  );

  const value = useMemo<AuthState>(
    () => ({ user, loading, login, logout, hasRole }),
    [user, loading, login, logout, hasRole]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}