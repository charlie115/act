"use client";

import { memo, useMemo } from "react";

function pc(v) {
  const n = Number(v || 0);
  if (n > 0) return "text-positive";
  if (n < 0) return "text-negative";
  return "text-ink-muted";
}

function fmtPct(v) {
  if (v === null || v === undefined) return "-";
  const n = Number(v);
  return `${n > 0 ? "+" : ""}${n.toFixed(2)}%`;
}

function Stat({ label, value, colorClass }) {
  return (
    <div className="flex items-center gap-1 sm:gap-1.5">
      <span className="text-[0.48rem] sm:text-[0.64rem] font-medium text-ink-muted/50">{label}</span>
      <span className={`text-[0.56rem] sm:text-xs tabular-nums font-bold ${colorClass}`}>{value}</span>
    </div>
  );
}

const TIME_FMT = new Intl.DateTimeFormat("ko-KR", { hour: "2-digit", minute: "2-digit", second: "2-digit" });

const MarketSummaryBar = memo(function MarketSummaryBar({ liveRows, connected, lastReceivedAt, volatilityMap = {} }) {
  const { btc, eth, avg } = useMemo(() => {
    const b = liveRows.find((r) => r.base_asset === "BTC");
    const e = liveRows.find((r) => r.base_asset === "ETH");
    let totalVol = 0, weightedSum = 0;
    for (const r of liveRows) {
      const ls = Number(r.LS_close || 0);
      const vol = Number(r.atp24h || 0);
      if (Number.isFinite(ls) && vol > 0) { weightedSum += ls * vol; totalVol += vol; }
    }
    return { btc: b, eth: e, avg: totalVol > 0 ? weightedSum / totalVol : null };
  }, [liveRows]);

  const highVol = useMemo(() => {
    let high = null;
    for (const [symbol, data] of Object.entries(volatilityMap)) {
      const md = Number(data?.mean_diff);
      if (!Number.isFinite(md)) continue;
      if (!high || md > Number(high.val)) high = { symbol, val: md };
    }
    return high;
  }, [volatilityMap]);

  const timeLabel = lastReceivedAt ? TIME_FMT.format(new Date(lastReceivedAt)) : null;

  return (
    <div className="flex items-center gap-2 sm:gap-4 overflow-x-auto scrollbar-hide rounded-lg border border-border/40 bg-surface-elevated/20 px-2 sm:px-3 py-1 sm:py-2 whitespace-nowrap">
      <Stat label="BTC" value={btc ? fmtPct(btc.LS_close) : "-"} colorClass={pc(btc?.LS_close)} />
      <div className="h-3 w-px bg-border/40" />
      <Stat label="ETH" value={eth ? fmtPct(eth.LS_close) : "-"} colorClass={pc(eth?.LS_close)} />
      <div className="h-3 w-px bg-border/40" />
      <Stat label="평균" value={avg !== null ? fmtPct(avg) : "-"} colorClass={pc(avg)} />
      {highVol ? (
        <>
          <div className="h-3 w-px bg-border/40" />
          <div className="flex">
            <Stat label="변동↑" value={`${highVol.symbol} ${Number(highVol.val).toFixed(2)}`} colorClass="text-positive" />
          </div>
        </>
      ) : null}
      <div className="ml-auto flex items-center gap-1.5 whitespace-nowrap">
        <span className={`inline-block h-1.5 w-1.5 rounded-full ${connected ? "bg-positive" : "bg-negative animate-pulse"}`} />
        <span className="text-[0.46rem] sm:text-[0.64rem] text-ink-muted/40">{connected ? "연결" : "재연결"}</span>
        {timeLabel ? <span className="text-[0.44rem] sm:text-[0.6rem] tabular-nums text-ink-muted/30">{timeLabel}</span> : null}
      </div>
    </div>
  );
});

export default MarketSummaryBar;
