"use client";

import { useEffect, useMemo, useState } from "react";

import ArbitrageLayout from "./ArbitrageLayout";

function formatPercent(value) {
  if (value === null || value === undefined) {
    return "-";
  }

  return `${Number(value).toFixed(4)}%`;
}

function polarityColor(value) {
  const n = Number(value || 0);
  if (n > 0) return "text-positive";
  if (n < 0) return "text-negative";
  return "text-ink-muted";
}

const LOOKBACK_OPTIONS = [
  { label: "최근 5회", value: "5" },
  { label: "최근 10회", value: "10" },
  { label: "최근 20회", value: "20" },
  { label: "최근 50회", value: "50" },
];

export default function ArbitrageAverageFundingRateClient() {
  const [lookback, setLookback] = useState(10);
  const [data, setData] = useState([]);
  const [pageError, setPageError] = useState("");

  useEffect(() => {
    let active = true;

    async function loadData() {
      setPageError("");

      try {
        const response = await fetch(`/api/infocore/funding-rate/average/?n=${lookback}`, {
          cache: "no-store",
        });

        if (!response.ok) {
          throw new Error("평균 펀딩비 데이터를 불러오지 못했습니다.");
        }

        const payload = await response.json();

        if (!active) {
          return;
        }

        setData(payload);
      } catch (requestError) {
        if (!active) {
          return;
        }

        setPageError(requestError.message);
      }
    }

    loadData();

    return () => {
      active = false;
    };
  }, [lookback]);

  const rows = useMemo(
    () => [...data].sort((left, right) => Number(right.funding_rate || 0) - Number(left.funding_rate || 0)),
    [data]
  );

  return (
    <ArbitrageLayout currentTab="avg">
      <div className="rounded-lg border border-border bg-background/92 p-4">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          <h2 className="text-sm font-bold text-ink">최근 평균 펀딩비</h2>
          <div className="flex items-center gap-1">
            {LOOKBACK_OPTIONS.map((option) => (
              <button
                key={option.value}
                className={`rounded-md px-2.5 py-1 text-xs font-bold transition-colors ${
                  String(lookback) === option.value
                    ? "bg-accent/15 text-accent"
                    : "text-ink-muted hover:bg-surface-elevated/40 hover:text-ink"
                }`}
                onClick={() => setLookback(Number(option.value))}
                type="button"
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>
        <div className="overflow-x-auto rounded-lg border border-border bg-background/90">
          <table className="w-full border-collapse">
            <thead>
              <tr className="border-b border-border">
                <th className="px-3 py-2 text-left text-[0.62rem] font-bold uppercase tracking-widest text-ink-muted">자산</th>
                <th className="px-3 py-2 text-left text-[0.62rem] font-bold uppercase tracking-widest text-ink-muted">시장</th>
                <th className="px-3 py-2 text-left text-[0.62rem] font-bold uppercase tracking-widest text-ink-muted">기준통화</th>
                <th className="px-3 py-2 text-right text-[0.62rem] font-bold uppercase tracking-widest text-ink-muted">평균 펀딩비</th>
              </tr>
            </thead>
            <tbody>
              {rows.length ? (
                rows.map((item, index) => (
                  <tr
                    key={`${item.market_code}-${item.base_asset}-${index}`}
                    className="border-t border-border/50 transition-colors hover:bg-surface-elevated/30"
                  >
                    <td className="px-3 py-2 text-sm font-semibold text-ink">{item.base_asset}</td>
                    <td className="px-3 py-2 text-xs text-ink-muted">{item.market_code}</td>
                    <td className="px-3 py-2 text-xs text-ink-muted">{item.quote_asset}</td>
                    <td className={`tabular-nums px-3 py-2 text-right font-mono text-sm font-semibold ${polarityColor(item.funding_rate)}`}>
                      {formatPercent(item.funding_rate)}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="4" className="px-4 py-8 text-center text-sm text-ink-muted">
                    평균 펀딩비 데이터가 없습니다.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        {pageError ? <p className="mt-3 text-sm text-negative">{pageError}</p> : null}
      </div>
    </ArbitrageLayout>
  );
}
