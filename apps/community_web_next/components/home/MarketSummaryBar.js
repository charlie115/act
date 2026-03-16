"use client";

import { useMemo } from "react";

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

function Pill({ label, value, colorClass, sub }) {
  return (
    <div className="flex items-center gap-1.5 rounded-lg bg-surface-elevated/40 px-2.5 py-1">
      <span className="text-[0.64rem] text-ink-muted/60">{label}</span>
      <strong className={`text-xs tabular-nums font-bold ${colorClass}`}>{value}</strong>
      {sub && <span className="text-[0.56rem] text-ink-muted/40">{sub}</span>}
    </div>
  );
}

const TIME_FMT = new Intl.DateTimeFormat("ko-KR", { hour: "2-digit", minute: "2-digit", second: "2-digit" });

export default function MarketSummaryBar({ liveRows, connected, lastReceivedAt, volatilityMap = {} }) {
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

  const { highVol, lowVol } = useMemo(() => {
    let high = null;
    let low = null;
    for (const [symbol, data] of Object.entries(volatilityMap)) {
      const md = Number(data?.mean_diff);
      if (!Number.isFinite(md)) continue;
      if (!high || md > Number(high.val)) high = { symbol, val: md };
      if (!low || md < Number(low.val)) low = { symbol, val: md };
    }
    return { highVol: high, lowVol: low };
  }, [volatilityMap]);

  const timeLabel = lastReceivedAt ? TIME_FMT.format(new Date(lastReceivedAt)) : null;

  return (
    <div className="flex flex-wrap items-center gap-1.5">
      <Pill label="BTC" value={btc ? fmtPct(btc.LS_close) : "-"} colorClass={pc(btc?.LS_close)} />
      <Pill label="ETH" value={eth ? fmtPct(eth.LS_close) : "-"} colorClass={pc(eth?.LS_close)} />
      <Pill label="평균" value={avg !== null ? fmtPct(avg) : "-"} colorClass={pc(avg)} />
      {highVol && (
        <div className="hidden sm:flex">
          <Pill label="변동↑" value={`${highVol.symbol} ${Number(highVol.val).toFixed(2)}`} colorClass="text-positive" />
        </div>
      )}
      {lowVol && (
        <div className="hidden sm:flex">
          <Pill label="변동↓" value={`${lowVol.symbol} ${Number(lowVol.val).toFixed(2)}`} colorClass="text-negative" />
        </div>
      )}
      <div className="ml-auto flex items-center gap-1 sm:gap-2 text-[0.58rem] sm:text-[0.68rem] text-ink-muted/50">
        <span className={`inline-block h-1.5 w-1.5 rounded-full ${connected ? "bg-positive" : "bg-negative animate-pulse"}`} />
        <span>{connected ? "연결됨" : "재연결 중"}</span>
        {timeLabel && <span className="tabular-nums">{timeLabel}</span>}
      </div>
    </div>
  );
}
