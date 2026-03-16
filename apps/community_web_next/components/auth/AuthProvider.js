"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

const AuthContext = createContext({
  user: null,
  token: null,
  loggedIn: false,
  loading: true,
  login: () => {},
  logout: () => {},
  authorizedRequest: () => {},
  authorizedListRequest: () => {},
});

export function useAuth() {
  return useContext(AuthContext);
}

export default function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const stored = localStorage.getItem("acw_auth");
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        setToken(parsed.access);
        setUser(parsed.user);
      } catch {}
    }
    setLoading(false);
  }, []);

  const clearError = useCallback(() => setError(null), []);

  const login = useCallback((authData) => {
    setToken(authData.access);
    setUser(authData.user);
    localStorage.setItem("acw_auth", JSON.stringify(authData));
  }, []);

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
    localStorage.removeItem("acw_auth");
  }, []);

  const authorizedRequest = useCallback(
    async (url, options = {}) => {
      if (!token) throw new Error("Not authenticated");
      const { body, ...rest } = options;
      const res = await fetch(`/api${url}`, {
        ...rest,
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
          ...rest.headers,
        },
        body: body ? JSON.stringify(body) : undefined,
      });
      if (res.status === 401) {
        logout();
        throw new Error("Session expired");
      }
      if (!res.ok) throw new Error(`Request failed: ${res.status}`);
      if (res.status === 204) return null;
      return res.json();
    },
    [token, logout],
  );

  const authorizedListRequest = useCallback(
    async (url) => {
      if (!token) return [];
      try {
        const data = await authorizedRequest(url);
        return Array.isArray(data) ? data : data?.results || [];
      } catch {
        return [];
      }
    },
    [token, authorizedRequest],
  );

  const signInWithGoogle = useCallback(
    async (googleAccessToken) => {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch("/api/auth/google/", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ access_token: googleAccessToken }),
        });
        if (!res.ok) {
          const data = await res.json().catch(() => ({}));
          throw new Error(data.detail || "Google 로그인 실패");
        }
        const authData = await res.json();
        login(authData);
      } catch (err) {
        setError(err.message);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [login],
  );

  const updateUser = useCallback(
    (patch) => {
      setUser((prev) => {
        const updated = { ...prev, ...patch };
        const stored = localStorage.getItem("acw_auth");
        if (stored) {
          const parsed = JSON.parse(stored);
          parsed.user = updated;
          localStorage.setItem("acw_auth", JSON.stringify(parsed));
        }
        return updated;
      });
    },
    [],
  );

  const registerUsername = useCallback(
    async (username) => {
      try {
        const res = await fetch("/api/users/register-username/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ username }),
        });
        if (!res.ok) {
          const data = await res.json().catch(() => ({}));
          throw new Error(data.detail || data.username?.[0] || "등록 실패");
        }
        const data = await res.json();
        setUser(data.user || { ...user, username });
        const stored = localStorage.getItem("acw_auth");
        if (stored) {
          const parsed = JSON.parse(stored);
          parsed.user = data.user || { ...user, username };
          localStorage.setItem("acw_auth", JSON.stringify(parsed));
        }
      } catch (err) {
        setError(err.message);
        throw err;
      }
    },
    [token, user],
  );

  const isReady = !loading;
  const isVisitor = Boolean(user && !user.username);
  const loggedIn = Boolean(token && user?.username);

  const value = useMemo(
    () => ({
      user,
      token,
      loggedIn,
      isReady,
      isVisitor,
      isLoading: loading,
      loading,
      error,
      clearError,
      login,
      logout,
      authorizedRequest,
      authorizedListRequest,
      signInWithGoogle,
      updateUser,
      registerUsername,
    }),
    [user, token, loggedIn, isReady, isVisitor, loading, error, clearError, login, logout, authorizedRequest, authorizedListRequest, signInWithGoogle, updateUser, registerUsername],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
