"use client";

function formatCompact(value, digits = 2) {
  if (value === null || value === undefined || value === "") return "-";
  const n = Number(value);
  const prefix = n > 0 ? "+" : "";
  return `${prefix}${n.toFixed(digits)}%`;
}

export default function MarketSummaryBar({ liveRows, connected, lastReceivedAt }) {
  const loading = !liveRows.length && !connected;
  const btcRow = liveRows.find((r) => r.base_asset === "BTC");
  const ethRow = liveRows.find((r) => r.base_asset === "ETH");

  const avgPremium =
    liveRows.length > 0
      ? liveRows.reduce((sum, r) => sum + Number(r.LS_close || 0), 0) / liveRows.length
      : null;

  const lastTimeLabel = lastReceivedAt
    ? new Intl.DateTimeFormat("ko-KR", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      }).format(new Date(lastReceivedAt))
    : null;

  const items = [
    {
      label: "BTC 김프",
      value: btcRow ? formatCompact(btcRow.LS_close) : "-",
      polarity: Number(btcRow?.LS_close || 0),
    },
    {
      label: "ETH 김프",
      value: ethRow ? formatCompact(ethRow.LS_close) : "-",
      polarity: Number(ethRow?.LS_close || 0),
    },
    {
      label: "평균 김프",
      value: avgPremium !== null ? formatCompact(avgPremium) : "-",
      polarity: avgPremium || 0,
    },
    {
      label: "연결 상태",
      value: connected ? "연결됨" : "재연결 중",
      sub: lastTimeLabel ? `마지막 ${lastTimeLabel}` : null,
      polarity: connected ? 1 : -1,
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-px overflow-hidden rounded-lg border border-border bg-border sm:grid-cols-4">
      {items.map((item) => (
        <div key={item.label} className="flex flex-col gap-1 bg-background/96 px-3 py-2.5">
          <span className="text-[0.56rem] font-bold uppercase tracking-[0.14em] text-accent">
            {item.label}
          </span>
          {loading ? (
            <div className="h-4 w-16 animate-pulse rounded bg-border/30" />
          ) : (
            <strong
              className={`tabular-nums text-sm font-bold ${
                item.polarity > 0
                  ? "text-positive"
                  : item.polarity < 0
                    ? "text-negative"
                    : "text-ink"
              }`}
            >
              {item.value}
            </strong>
          )}
          {item.sub ? (
            <small className="text-[0.72rem] text-ink-muted">{item.sub}</small>
          ) : null}
        </div>
      ))}
    </div>
  );
}
