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

export default function ArbitrageFundingRateDiffClient() {
  const [data, setData] = useState([]);
  const [pageError, setPageError] = useState("");
  const [sameExchangeOnly, setSameExchangeOnly] = useState(false);

  useEffect(() => {
    let active = true;

    async function loadData() {
      setPageError("");

      try {
        const response = await fetch("/api/infocore/funding-rate/diff/", {
          cache: "no-store",
        });

        if (!response.ok) {
          throw new Error("펀딩비 차이 데이터를 불러오지 못했습니다.");
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
  }, []);

  const rows = useMemo(() => {
    let filtered = [...data];

    if (sameExchangeOnly) {
      filtered = filtered.filter(
        (item) => item.exchange_x === item.exchange_y
      );
    }

    return filtered.sort(
      (left, right) =>
        Math.abs(Number(right.funding_rate_diff || 0)) -
        Math.abs(Number(left.funding_rate_diff || 0))
    );
  }, [data, sameExchangeOnly]);

  return (
    <ArbitrageLayout currentTab="diff">
      <div className="rounded-lg border border-border bg-background/92 p-4">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          <h2 className="text-sm font-bold text-ink">거래소 간 펀딩비 차이</h2>
          <div className="flex items-center gap-3">
            <label className="inline-flex cursor-pointer items-center gap-1.5 text-[0.7rem] sm:text-sm text-ink-muted">
              <input
                checked={sameExchangeOnly}
                className="accent-accent"
                onChange={(event) => setSameExchangeOnly(event.target.checked)}
                type="checkbox"
              />
              같은 거래소끼리만
            </label>
            <span className="rounded bg-accent/10 px-2 py-0.5 text-[0.66rem] font-bold tabular-nums text-accent">
              {rows.length}건
            </span>
          </div>
        </div>
        <div className="overflow-x-auto rounded-lg border border-border bg-background/90">
          <table className="w-full border-collapse">
            <thead>
              <tr className="border-b border-border">
                <th className="px-3 py-2 text-left text-[0.62rem] font-bold uppercase tracking-widest text-ink-muted">자산</th>
                <th className="px-3 py-2 text-left text-[0.62rem] font-bold uppercase tracking-widest text-ink-muted">시장 X</th>
                <th className="px-3 py-2 text-right text-[0.62rem] font-bold uppercase tracking-widest text-ink-muted">펀딩 X</th>
                <th className="px-3 py-2 text-left text-[0.62rem] font-bold uppercase tracking-widest text-ink-muted">시장 Y</th>
                <th className="px-3 py-2 text-right text-[0.62rem] font-bold uppercase tracking-widest text-ink-muted">펀딩 Y</th>
                <th className="px-3 py-2 text-right text-[0.62rem] font-bold uppercase tracking-widest text-ink-muted">차이</th>
              </tr>
            </thead>
            <tbody>
              {rows.length ? (
                rows.map((item, index) => (
                  <tr
                    key={`${item.base_asset}-${item.market_code_x}-${item.market_code_y}-${index}`}
                    className="border-t border-border/50 transition-colors hover:bg-surface-elevated/30"
                  >
                    <td className="px-3 py-2 text-sm font-semibold text-ink">{item.base_asset}</td>
                    <td className="px-3 py-2 text-xs text-ink-muted">{item.exchange_x} / {item.market_code_x}</td>
                    <td className={`tabular-nums px-3 py-2 text-right font-mono text-sm ${polarityColor(item.funding_rate_x)}`}>
                      {formatPercent(item.funding_rate_x)}
                    </td>
                    <td className="px-3 py-2 text-xs text-ink-muted">{item.exchange_y} / {item.market_code_y}</td>
                    <td className={`tabular-nums px-3 py-2 text-right font-mono text-sm ${polarityColor(item.funding_rate_y)}`}>
                      {formatPercent(item.funding_rate_y)}
                    </td>
                    <td className={`tabular-nums px-3 py-2 text-right font-mono text-sm font-semibold ${polarityColor(item.funding_rate_diff)}`}>
                      {formatPercent(item.funding_rate_diff)}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="6" className="px-4 py-8 text-center text-sm text-ink-muted">
                    펀딩비 차이 데이터가 없습니다.
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
