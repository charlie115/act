"use client";

import { useEffect, useState } from "react";
import { useAuth } from "../auth/AuthProvider";

export default function BotApiKeyClient({ marketCodeCombination }) {
  const { authorizedRequest, loggedIn } = useAuth();
  const [apiKeys, setApiKeys] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!loggedIn) return;
    authorizedRequest("/tradecore/api-keys/")
      .then((data) => setApiKeys(Array.isArray(data) ? data : data?.results || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [loggedIn, authorizedRequest]);

  if (loading) return <div className="grid place-items-center py-8"><div className="h-6 w-6 animate-spin rounded-full border-2 border-border border-t-accent" /></div>;

  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold text-ink">API 키 관리</h3>
      {apiKeys.length === 0 ? (
        <p className="text-sm text-ink-muted py-4 text-center">등록된 API 키가 없습니다.</p>
      ) : (
        <div className="space-y-2">
          {apiKeys.map((key) => (
            <div key={key.id} className="flex items-center justify-between rounded-lg border border-border/50 bg-background p-3">
              <div>
                <p className="text-sm font-medium text-ink">{key.exchange}</p>
                <p className="text-xs text-ink-muted">{key.api_key?.slice(0, 8)}...{key.api_key?.slice(-4)}</p>
              </div>
              <span className={`text-xs ${key.is_active ? "text-positive" : "text-negative"}`}>{key.is_active ? "활성" : "비활성"}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
