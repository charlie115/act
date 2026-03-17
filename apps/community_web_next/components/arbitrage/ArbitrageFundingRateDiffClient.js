"use client";

import { useEffect, useMemo, useState } from "react";
import { Search } from "lucide-react";

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

function diffBg(value) {
  const n = Math.abs(Number(value || 0));
  if (n >= 0.001) return "bg-opportunity/10";
  if (n >= 0.0005) return "bg-opportunity/5";
  return "";
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

const TH = "sticky top-0 z-[1] bg-background px-3 py-2.5 text-[0.6rem] font-bold uppercase tracking-wider text-ink-muted/60 whitespace-nowrap";
const TD = "px-2 py-1.5 tabular-nums whitespace-nowrap text-[0.7rem] sm:text-xs";

export default function ArbitrageFundingRateDiffClient() {
  const [data, setData] = useState([]);
  const [pageError, setPageError] = useState("");
  const [sameExchangeOnly, setSameExchangeOnly] = useState(false);
  const [query, setQuery] = useState("");
  const [sortKey, setSortKey] = useState("diff");
  const [sortDir, setSortDir] = useState("desc");

  function toggleSort(key) {
    if (sortKey === key) {
      setSortDir(d => d === "desc" ? "asc" : "desc");
    } else {
      setSortKey(key);
      setSortDir("desc");
    }
  }

  useEffect(() => {
    let active = true;

    async function loadData() {
      setPageError("");
      try {
        const response = await fetch("/api/infocore/funding-rate/diff/", { cache: "no-store" });
        if (!response.ok) throw new Error("펀딩비 차이 데이터를 불러오지 못했습니다.");
        const payload = await response.json();
        if (active) setData(payload);
      } catch (err) {
        if (active) setPageError(err.message);
      }
    }

    loadData();
    return () => { active = false; };
  }, []);

  const rows = useMemo(() => {
    let filtered = [...data];
    if (sameExchangeOnly) {
      filtered = filtered.filter((item) => item.exchange_x === item.exchange_y);
    }
    if (query.trim()) {
      const q = query.trim().toLowerCase();
      filtered = filtered.filter((item) => item.base_asset?.toLowerCase().includes(q));
    }
    const accessor = { fx: r => Number(r.funding_rate_x || 0), fy: r => Number(r.funding_rate_y || 0), diff: r => Number(r.funding_rate_diff || 0) };
    const fn = accessor[sortKey] || accessor.diff;
    return filtered.sort((a, b) => sortDir === "desc" ? fn(b) - fn(a) : fn(a) - fn(b));
  }, [data, sameExchangeOnly, query, sortKey, sortDir]);

  return (
    <ArbitrageLayout currentTab="diff">
      <div className="rounded-lg border border-border bg-background/92">
        {/* Toolbar */}
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border/50 px-4 py-2.5">
          <div className="flex items-center gap-3">
            <h2 className="text-sm font-bold text-ink">거래소 간 펀딩비 차이</h2>
            <span className="rounded bg-accent/10 px-2 py-0.5 text-[0.66rem] font-bold tabular-nums text-accent">
              {rows.length}건
            </span>
          </div>
          <div className="flex items-center gap-2">
            <label className="inline-flex cursor-pointer items-center gap-1.5 rounded-lg border border-border bg-background/70 px-2.5 py-1.5 text-[0.7rem] text-ink-muted transition-colors hover:border-accent/30">
              <input
                checked={sameExchangeOnly}
                className="accent-accent"
                onChange={(e) => setSameExchangeOnly(e.target.checked)}
                type="checkbox"
              />
              같은 거래소끼리만
            </label>
            <div className="relative">
              <Search className="pointer-events-none absolute left-2 top-1/2 -translate-y-1/2 text-ink-muted/50" size={13} />
              <input
                className="w-[140px] rounded-lg border border-border bg-background/80 py-1.5 pl-7 pr-2 text-xs text-ink placeholder:text-ink-muted/40 outline-none focus:border-accent/40"
                onChange={(e) => setQuery(e.target.value)}
                placeholder="자산 검색"
                value={query}
              />
            </div>
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full min-w-[520px]">
            <thead>
              <tr className="border-b-2 border-border/60">
                <th className={`${TH} text-left`}>자산</th>
                <th className={`${TH} text-left`}>시장 X</th>
                <th className={`${TH} text-right cursor-pointer`} onClick={() => toggleSort("fx")}>
                  펀딩 X {sortKey === "fx" ? (sortDir === "desc" ? "↓" : "↑") : ""}
                </th>
                <th className={`${TH} text-left`}>시장 Y</th>
                <th className={`${TH} text-right cursor-pointer`} onClick={() => toggleSort("fy")}>
                  펀딩 Y {sortKey === "fy" ? (sortDir === "desc" ? "↓" : "↑") : ""}
                </th>
                <th className={`${TH} text-right cursor-pointer`} onClick={() => toggleSort("diff")}>
                  차이 {sortKey === "diff" ? (sortDir === "desc" ? "↓" : "↑") : ""}
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/20">
              {rows.length ? (
                rows.map((item, i) => (
                  <tr
                    key={`${item.base_asset}-${item.market_code_x}-${item.market_code_y}-${i}`}
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
                        <ExIcon name={item.exchange_x} />
                        {item.market_code_x?.replace(item.exchange_x + "_", "")}
                      </span>
                    </td>
                    <td className={`${TD} text-right text-xs ${pc(item.funding_rate_x)}`}>
                      {fmtPct(item.funding_rate_x)}
                    </td>
                    <td className={`${TD} text-xs text-ink-muted`}>
                      <span className="inline-flex items-center gap-1.5">
                        <ExIcon name={item.exchange_y} />
                        {item.market_code_y?.replace(item.exchange_y + "_", "")}
                      </span>
                    </td>
                    <td className={`${TD} text-right text-xs ${pc(item.funding_rate_y)}`}>
                      {fmtPct(item.funding_rate_y)}
                    </td>
                    <td className={`${TD} text-right text-sm font-bold ${pc(item.funding_rate_diff)} ${diffBg(item.funding_rate_diff)}`}>
                      {fmtPct(item.funding_rate_diff)}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="6" className="px-4 py-12 text-center text-sm text-ink-muted">
                    펀딩비 차이 데이터가 없습니다.
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
