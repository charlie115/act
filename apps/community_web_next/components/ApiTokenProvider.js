"use client";

import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";
import { refreshApiToken } from "../lib/actions/refreshApiToken";
import { setGlobalApiToken } from "../lib/clientCache";

const ApiTokenContext = createContext("");

const REFRESH_INTERVAL_MS = 4 * 60 * 1000; // Refresh every 4 min (token TTL = 5 min)

export function ApiTokenProvider({ initialToken, children }) {
  const [token, setToken] = useState(initialToken || "");
  const refreshTimerRef = useRef(null);

  const refresh = useCallback(async () => {
    try {
      const next = await refreshApiToken();
      setGlobalApiToken(next);
      setToken(next);
    } catch {
      // keep current token on failure
    }
  }, []);

  // Sync token to global store whenever it changes
  useEffect(() => {
    if (token) setGlobalApiToken(token);
  }, [token]);

  // Schedule periodic refresh
  useEffect(() => {
    refreshTimerRef.current = setInterval(refresh, REFRESH_INTERVAL_MS);
    return () => clearInterval(refreshTimerRef.current);
  }, [refresh]);

  // If no initial token, fetch one on mount
  useEffect(() => {
    if (!initialToken) {
      refresh();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <ApiTokenContext.Provider value={token}>
      {children}
    </ApiTokenContext.Provider>
  );
}

export function useApiToken() {
  return useContext(ApiTokenContext);
}
