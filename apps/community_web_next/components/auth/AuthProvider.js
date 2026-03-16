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

  const value = useMemo(
    () => ({
      user,
      token,
      loggedIn: Boolean(token),
      loading,
      login,
      logout,
      authorizedRequest,
      authorizedListRequest,
    }),
    [user, token, loading, login, logout, authorizedRequest, authorizedListRequest],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
