"use client";

import { useEffect, useMemo, useState } from "react";

import ArbitrageLayout from "./ArbitrageLayout";

const MINIO_BASE = process.env.NEXT_PUBLIC_MINIO_URL || "http://localhost:19000";
const ASSET_ICON_PATH = `${MINIO_BASE}/community-media/assets/icons`;

function AssetIcon({ symbol, size = 18 }) {
  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img alt={symbol} className="rounded-full" height={size} width={size}
      src={`${ASSET_ICON_PATH}/${symbol}.PNG`}
      onError={(e) => { e.currentTarget.style.display = "none"; if (e.currentTarget.nextSibling) e.currentTarget.nextSibling.style.display = "flex"; }}
      style={{ objectFit: "cover" }} />
  );
}

function AssetBadge({ symbol, size = 18 }) {
  const bg = `hsl(${[...symbol].reduce((a, c) => a + c.charCodeAt(0), 0) % 360}, 55%, 42%)`;
  return (
    <span className="inline-flex flex-shrink-0">
      <AssetIcon symbol={symbol} size={size} />
      <span className="items-center justify-center rounded-full font-bold text-white"
        style={{ width: size, height: size, fontSize: size * 0.42, backgroundColor: bg, display: "none" }}>
        {symbol.slice(0, 1)}
      </span>
    </span>
  );
}

function fmtPct(value) {
  if (value === null || value === undefined) return "-";
  return `${Number(value).toFixed(4)}%`;
}

function pc(value) {
  const n = Number(value || 0);
  if (n > 0) return "text-positive";
  if (n < 0) return "text-negative";
  return "text-ink-muted";
}

function ExIcon({ name, size = 14 }) {
  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      alt={name}
      className="inline-block rounded-sm"
      height={size}
      width={size}
      src={`/images/exchanges/${(name || "").toLowerCase()}.svg`}
      onError={(e) => { e.currentTarget.style.display = "none"; }}
    />
  );
}

function FundingBar({ value, maxAbs }) {
  const n = Number(value || 0);
  const pct = Math.min(100, (Math.abs(n) / maxAbs) * 100);
  const color = n >= 0 ? "bg-positive/40" : "bg-negative/40";
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-10 sm:w-16 rounded-full bg-border/30 overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

const LOOKBACK_OPTIONS = [
  { label: "5회", value: "5" },
  { label: "10회", value: "10" },
  { label: "20회", value: "20" },
  { label: "50회", value: "50" },
];

const TH = "sticky top-0 z-[1] bg-background px-3 py-2.5 text-[0.6rem] font-bold uppercase tracking-wider text-ink-muted/60 whitespace-nowrap";
const TD = "px-2 py-1.5 tabular-nums whitespace-nowrap text-[0.7rem] sm:text-xs";

export default function ArbitrageAverageFundingRateClient() {
  const [lookback, setLookback] = useState(10);
  const [data, setData] = useState([]);
  const [pageError, setPageError] = useState("");

  useEffect(() => {
    let active = true;

    async function loadData() {
      setPageError("");
      try {
        const response = await fetch(`/api/infocore/funding-rate/average/?n=${lookback}`, { cache: "no-store" });
        if (!response.ok) throw new Error("평균 펀딩비 데이터를 불러오지 못했습니다.");
        const payload = await response.json();
        if (active) setData(payload);
      } catch (err) {
        if (active) setPageError(err.message);
      }
    }

    loadData();
    return () => { active = false; };
  }, [lookback]);

  const rows = useMemo(
    () => [...data].sort((a, b) => Number(b.funding_rate || 0) - Number(a.funding_rate || 0)),
    [data]
  );

  const maxAbs = useMemo(
    () => rows.reduce((max, r) => Math.max(max, Math.abs(Number(r.funding_rate || 0))), 0.0001),
    [rows]
  );

  return (
    <ArbitrageLayout currentTab="avg">
      <div className="rounded-lg border border-border bg-background/92">
        {/* Toolbar */}
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border/50 px-4 py-2.5">
          <h2 className="text-sm font-bold text-ink">최근 평균 펀딩비</h2>
          <div className="flex rounded-lg border border-border bg-background/70 p-0.5">
            {LOOKBACK_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                className={`rounded-md px-2.5 py-1 text-xs font-bold transition-all ${
                  String(lookback) === opt.value
                    ? "bg-accent/15 text-accent shadow-sm"
                    : "text-ink-muted hover:text-ink"
                }`}
                onClick={() => setLookback(Number(opt.value))}
                type="button"
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full min-w-[400px]">
            <thead>
              <tr className="border-b-2 border-border/60">
                <th className={`${TH} text-left`}>자산</th>
                <th className={`${TH} text-left`}>시장</th>
                <th className={`${TH} text-right`}>평균 펀딩비</th>
                <th className={`${TH} text-left`} />
              </tr>
            </thead>
            <tbody className="divide-y divide-border/20">
              {rows.length ? (
                rows.map((item, i) => {
                  const exchange = item.market_code?.split("_")[0] || "";
                  const marketType = item.market_code?.split("_").slice(1).join("-") || "";
                  return (
                    <tr
                      key={`${item.market_code}-${item.base_asset}-${i}`}
                      className="transition-colors hover:bg-surface-elevated/30"
                    >
                      <td className={`${TD} text-sm font-semibold text-ink`}>
                        <span className="inline-flex items-center gap-1.5">
                          <AssetBadge symbol={item.base_asset} size={18} />
                          {item.base_asset}
                        </span>
                      </td>
                      <td className={`${TD} text-xs text-ink-muted`}>
                        <span className="inline-flex items-center gap-1.5">
                          <ExIcon name={exchange} />
                          {marketType.replace(/_/g, "-")}
                        </span>
                      </td>
                      <td className={`${TD} text-right text-sm font-bold ${pc(item.funding_rate)}`}>
                        {fmtPct(item.funding_rate)}
                      </td>
                      <td className={TD}>
                        <FundingBar value={item.funding_rate} maxAbs={maxAbs} />
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan="4" className="px-4 py-12 text-center text-sm text-ink-muted">
                    평균 펀딩비 데이터가 없습니다.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        {pageError ? <p className="px-4 py-3 text-sm text-negative">{pageError}</p> : null}
      </div>
    </ArbitrageLayout>
  );
}
