"use client";

import { useEffect, useState } from "react";
import { useAuth } from "../auth/AuthProvider";

export default function BotPnlHistoryClient({ marketCodeCombination }) {
  const { authorizedRequest, loggedIn } = useAuth();
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!loggedIn) return;
    authorizedRequest("/tradecore/pnl-history/")
      .then((data) => setHistory(Array.isArray(data) ? data : data?.results || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [loggedIn, authorizedRequest]);

  if (loading) return <div className="grid place-items-center py-8"><div className="h-6 w-6 animate-spin rounded-full border-2 border-border border-t-accent" /></div>;

  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold text-ink">손익 히스토리</h3>
      {history.length === 0 ? (
        <p className="text-sm text-ink-muted py-8 text-center">손익 기록이 없습니다.</p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-border">
          <table className="w-full text-sm">
            <thead><tr className="border-b border-border bg-background/50"><th className="px-3 py-2 text-left text-xs text-ink-muted">일시</th><th className="px-3 py-2 text-right text-xs text-ink-muted">손익</th></tr></thead>
            <tbody>
              {history.map((h) => (
                <tr key={h.id} className="border-b border-border/30">
                  <td className="px-3 py-2 text-ink-muted">{new Date(h.created_at).toLocaleDateString("ko-KR")}</td>
                  <td className={`px-3 py-2 text-right font-medium ${h.pnl >= 0 ? "text-positive" : "text-negative"}`}>{h.pnl > 0 ? "+" : ""}{Number(h.pnl).toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
