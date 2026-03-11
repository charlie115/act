"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

import { USER_ROLE } from "../../lib/constants";

const STORAGE_KEY = "acw-next-auth";

const AuthContext = createContext(null);

function readStoredSession() {
  if (typeof window === "undefined") {
    return null;
  }

  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function writeStoredSession(session) {
  if (typeof window === "undefined") {
    return;
  }

  if (!session) {
    window.localStorage.removeItem(STORAGE_KEY);
    return;
  }

  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
}

async function requestJson(pathname, { method = "GET", body, accessToken } = {}) {
  const response = await fetch(`/api${pathname}`, {
    method,
    headers: {
      "Content-Type": "application/json",
      ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  });

  let payload = null;

  try {
    payload = await response.json();
  } catch {
    payload = null;
  }

  if (!response.ok) {
    const error = new Error(payload?.detail || payload?.message || "Request failed");
    error.status = response.status;
    error.payload = payload;
    throw error;
  }

  return payload;
}

function normalizeListPayload(payload) {
  if (Array.isArray(payload)) {
    return payload;
  }

  if (Array.isArray(payload?.results)) {
    return payload.results;
  }

  return [];
}

export default function AuthProvider({ children }) {
  const [isReady, setIsReady] = useState(false);
  const [tokens, setTokens] = useState(null);
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const clearSession = useCallback(() => {
    setTokens(null);
    setUser(null);
    writeStoredSession(null);
  }, []);

  const persistSession = useCallback((nextTokens, nextUser) => {
    setTokens(nextTokens);
    setUser(nextUser);
    writeStoredSession({ tokens: nextTokens, user: nextUser });
  }, []);

  const refreshAccessToken = useCallback(
    async (refreshToken) => {
      const payload = await requestJson("/auth/token/refresh/", {
        method: "POST",
        body: { refresh: refreshToken },
      });

      const nextTokens = {
        accessToken: payload.access,
        refreshToken,
      };

      setTokens(nextTokens);
      writeStoredSession({ tokens: nextTokens, user });
      return nextTokens;
    },
    [user]
  );

  const fetchCurrentUser = useCallback(
    async (activeTokens) => {
      try {
        const nextUser = await requestJson("/auth/user/", {
          accessToken: activeTokens.accessToken,
        });
        persistSession(activeTokens, nextUser);
        return nextUser;
      } catch (requestError) {
        if (requestError.status !== 401 || !activeTokens.refreshToken) {
          throw requestError;
        }

        const refreshedTokens = await refreshAccessToken(activeTokens.refreshToken);
        const nextUser = await requestJson("/auth/user/", {
          accessToken: refreshedTokens.accessToken,
        });
        persistSession(refreshedTokens, nextUser);
        return nextUser;
      }
    },
    [persistSession, refreshAccessToken]
  );

  useEffect(() => {
    const session = readStoredSession();

    if (!session?.tokens) {
      setIsReady(true);
      return;
    }

    setTokens(session.tokens);
    setUser(session.user || null);

    fetchCurrentUser(session.tokens)
      .catch(() => {
        clearSession();
      })
      .finally(() => {
        setIsReady(true);
      });
  }, [clearSession, fetchCurrentUser]);

  const signInWithGoogle = useCallback(
    async (googleAccessToken) => {
      setIsLoading(true);
      setError("");

      try {
        const payload = await requestJson("/auth/login/", {
          method: "POST",
          body: { access_token: googleAccessToken },
        });

        const nextTokens = {
          accessToken: payload.access,
          refreshToken: payload.refresh,
        };

        persistSession(nextTokens, payload.user);
        return payload.user;
      } catch (requestError) {
        setError("Unable to authenticate the account. Please try again.");
        throw requestError;
      } finally {
        setIsLoading(false);
      }
    },
    [persistSession]
  );

  const registerUsername = useCallback(
    async (username) => {
      if (!tokens?.accessToken) {
        throw new Error("Missing access token");
      }

      setIsLoading(true);
      setError("");

      try {
        const nextUser = await requestJson("/auth/user/register/", {
          method: "PATCH",
          body: { username },
          accessToken: tokens.accessToken,
        });

        persistSession(tokens, nextUser);
        return nextUser;
      } catch (requestError) {
        setError("Username is not available. Please try again.");
        throw requestError;
      } finally {
        setIsLoading(false);
      }
    },
    [persistSession, tokens]
  );

  const signOut = useCallback(async () => {
    try {
      if (tokens?.accessToken) {
        await requestJson("/auth/logout/", {
          method: "POST",
          accessToken: tokens.accessToken,
        });
      }
    } catch {
      // Best effort logout.
    } finally {
      clearSession();
    }
  }, [clearSession, tokens]);

  const authorizedRequest = useCallback(
    async (pathname, options = {}) => {
      if (!tokens?.accessToken) {
        throw new Error("Missing access token");
      }

      try {
        return await requestJson(pathname, {
          ...options,
          accessToken: tokens.accessToken,
        });
      } catch (requestError) {
        if (requestError.status !== 401 || !tokens.refreshToken) {
          throw requestError;
        }

        const refreshedTokens = await refreshAccessToken(tokens.refreshToken);
        return requestJson(pathname, {
          ...options,
          accessToken: refreshedTokens.accessToken,
        });
      }
    },
    [refreshAccessToken, tokens]
  );

  const authorizedListRequest = useCallback(
    async (pathname, options = {}) => {
      const payload = await authorizedRequest(pathname, options);
      return normalizeListPayload(payload);
    },
    [authorizedRequest]
  );

  const updateUser = useCallback(
    (updates) => {
      setUser((currentUser) => {
        const nextUser = currentUser ? { ...currentUser, ...updates } : currentUser;
        writeStoredSession({ tokens, user: nextUser });
        return nextUser;
      });
    },
    [tokens]
  );

  const value = useMemo(
    () => ({
      isReady,
      isLoading,
      user,
      tokens,
      error,
      clearError: () => setError(""),
      loggedIn: Boolean(user && user.role !== USER_ROLE.visitor),
      isVisitor: Boolean(user && user.role === USER_ROLE.visitor),
      signInWithGoogle,
      registerUsername,
      signOut,
      updateUser,
      authorizedRequest,
      authorizedListRequest,
      refreshUser: async () => {
        if (!tokens) {
          return null;
        }

        return fetchCurrentUser(tokens);
      },
    }),
    [
      error,
      fetchCurrentUser,
      isLoading,
      isReady,
      registerUsername,
      signInWithGoogle,
      signOut,
      updateUser,
      authorizedRequest,
      authorizedListRequest,
      tokens,
      user,
    ]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }

  return context;
}
