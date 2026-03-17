"use client";

import { Fragment, memo, useCallback, useEffect, useMemo, useState } from "react";
import { ChevronDown, ChevronRight, ChevronUp } from "lucide-react";

import { premiumHeatmap, spreadHeatmap } from "../../lib/heatmap";
import PremiumChartPanel from "./PremiumChartPanel";

const MINIO_BASE = process.env.NEXT_PUBLIC_MINIO_URL || "http://localhost:19000";
const ASSET_ICON_PATH = `${MINIO_BASE}/community-media/assets/icons`;

function AssetIcon({ symbol, size = 14 }) {
  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img alt={symbol} className="rounded-full" height={size} width={size}
      src={`${ASSET_ICON_PATH}/${symbol}.PNG`}
      onError={(e) => { e.currentTarget.style.display = "none"; if (e.currentTarget.nextSibling) e.currentTarget.nextSibling.style.display = "flex"; }}
      style={{ objectFit: "cover" }} />
  );
}

function AssetBadge({ symbol, size = 14 }) {
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

function ExIcon({ exchange, size = 14 }) {
  const key = exchange?.toLowerCase() || "";
  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img alt={exchange} src={`/images/exchanges/${key}.svg`} width={size} height={size}
      className="inline rounded-sm" onError={(e) => { e.currentTarget.style.display = "none"; }} />
  );
}

const PAGE_SIZE = 50;
function fmt(v, d = 2, m = 0) { if (v == null || v === "") return "-"; return new Intl.NumberFormat("en-US", { maximumFractionDigits: d, minimumFractionDigits: m }).format(Number(v)); }
function fmtVol(v) { const n = Number(v || 0); if (!Number.isFinite(n)) return "-"; if (Math.abs(n) >= 1e8) return `${(n/1e8).toFixed(1)}억`; if (Math.abs(n) >= 1e4) return `${(n/1e4).toFixed(0)}만`; return fmt(n, 0); }
function pc(v) { const n = Number(v || 0); return n > 0 ? "text-positive" : n < 0 ? "text-negative" : "text-ink-muted"; }

const ACCESSORS = { asset: r => r.base_asset||"", price: r => Number(r.tp||0), enter: r => Number(r.LS_close||0), exit: r => Number(r.SL_close||0), spread: r => Number(r.SL_close||0)-Number(r.LS_close||0), volume: r => Number(r.atp24h||0) };
function doSort(rows, key, dir, favSet) {
  if (!key || !ACCESSORS[key]) return rows;
  return [...rows].sort((a, b) => {
    const af = favSet.has(a.base_asset), bf = favSet.has(b.base_asset);
    if (af && !bf) return -1; if (!af && bf) return 1;
    const av = ACCESSORS[key](a), bv = ACCESSORS[key](b);
    if (key === "asset") { const c = String(av).localeCompare(String(bv)); return dir === "asc" ? c : -c; }
    return dir === "asc" ? av - bv : bv - av;
  });
}

const TD = "px-0.5 py-1 sm:px-2 sm:py-1.5 lg:px-3";
const TDM = `${TD} tabular-nums`;
const IBADGE = { 1: "bg-green-500", 2: "bg-blue-500", 4: "bg-amber-500", 8: "bg-purple-500" };

function FundingCountdown({ fundingTime }) {
  const [now, setNow] = useState(Date.now);
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);
  const diff = new Date(fundingTime).getTime() - now;
  if (diff <= 0) return null;
  const h = Math.floor(diff / 3600000);
  const m = Math.floor((diff % 3600000) / 60000);
  const s = Math.floor((diff % 60000) / 1000);
  return <div className="text-[0.46rem] sm:text-[0.55rem] text-ink-muted/50 italic tabular-nums whitespace-nowrap">{h}시간 {String(m).padStart(2,"0")}분 {String(s).padStart(2,"0")}초 남음</div>;
}

function FundingCell({ fi }) {
  if (!fi) return <td className={`${TDM} text-right text-[0.56rem] sm:text-xs text-ink-muted/40 table-cell`}>-</td>;
  const rate = Number(fi.funding_rate || 0);
  const pct = (rate * 100).toFixed(3);
  const intH = fi.funding_interval_hours;
  const badge = IBADGE[intH] || "bg-blue-500";
  return (
    <td className={`${TDM} text-right text-[0.56rem] sm:text-xs table-cell`}>
      <div className="flex items-center justify-end gap-1">
        <span className={pc(rate)}>{pct}</span>
        {intH != null && <span className={`rounded px-1 py-px text-[0.42rem] sm:text-[0.5rem] font-bold text-white leading-none ${badge}`}>{intH}h</span>}
      </div>
      {fi.funding_time && <FundingCountdown fundingTime={fi.funding_time} />}
    </td>
  );
}

function WalletCell({ walletData, targetMarketCode, originMarketCode }) {
  if (!walletData || !targetMarketCode || !originMarketCode) {
    return <td className={`${TD} text-center text-ink-muted/25 table-cell`}>-</td>;
  }
  const bothSpot = targetMarketCode.includes("SPOT") && originMarketCode.includes("SPOT");
  const tEx = targetMarketCode.split("_")[0];
  const oEx = originMarketCode.split("_")[0];
  const tW = walletData[tEx]?.withdraw || [];
  const tD = walletData[tEx]?.deposit || [];
  const oW = walletData[oEx]?.withdraw || [];
  const oD = walletData[oEx]?.deposit || [];

  let canRight, canLeft;
  if (bothSpot) {
    // 현물↔현물: 출금→입금 네트워크 교집합
    canRight = tW.some(n => oD.includes(n));
    canLeft = oW.some(n => tD.includes(n));
  } else {
    // 현물↔선물: 전체 네트워크 합집합 존재 여부 (레거시 동일)
    const all = [...new Set([...tD, ...tW, ...oD, ...oW])];
    canRight = all.length > 0;
    canLeft = all.length > 0;
  }

  return (
    <td className={`${TD} text-center table-cell`}>
      <div className="flex flex-col items-center leading-none">
        <span className={`text-[0.7rem] ${canRight ? "text-positive" : "text-negative/40"}`}>→</span>
        <span className={`text-[0.7rem] ${canLeft ? "text-positive" : "text-negative/40"}`}>←</span>
      </div>
    </td>
  );
}

const Row = memo(function Row({ asset, row, expanded, favActive, loggedIn, onSelect, onFav, targetFI, originFI, volDiff, targetIsSpot, originIsSpot, walletData, targetMC, originMC }) {
  const ls = Number(row.LS_close || 0), sl = Number(row.SL_close || 0), spread = sl - ls;
  return (
    <tr className={`cursor-pointer transition-colors hover:bg-surface-elevated/40 ${expanded ? "bg-surface-elevated/20" : ""}`} onClick={() => onSelect(asset)}>
      <td className={`${TD} hidden sm:table-cell w-7`}>
        <button className={`text-xs ${favActive ? "text-opportunity" : "text-ink-muted/30 hover:text-ink-muted/60"} disabled:opacity-30`} disabled={!loggedIn} onClick={e => { e.stopPropagation(); onFav(asset); }} type="button">★</button>
      </td>
      <td className={TD}>
        <div className="flex items-center gap-1.5">
          <AssetBadge symbol={asset} size={16} />
          <strong className="text-[0.6rem] sm:text-xs text-ink">{asset}</strong>
          <ChevronRight size={8} strokeWidth={2.5} className={`flex-shrink-0 text-ink-muted/40 transition-transform hidden sm:inline-block ${expanded ? "rotate-90 text-accent" : ""}`} />
        </div>
      </td>
      <WalletCell walletData={walletData} targetMarketCode={targetMC} originMarketCode={originMC} />
      <td className={`${TDM} text-right whitespace-nowrap`}>
        <div className="flex items-baseline justify-end gap-1"><span className="text-[0.58rem] sm:text-xs font-semibold text-ink">{fmt(row.tp, row.tp >= 10000 ? 0 : 1)}</span><span className={`rounded px-1 py-px text-[0.5rem] sm:text-[0.56rem] font-semibold leading-none ${Number(row.scr) >= 0 ? "bg-positive/10 text-positive" : "bg-negative/10 text-negative"}`}>{row.scr > 0 ? "+" : ""}{fmt(row.scr, 2, 2)}%</span></div>
        {row.converted_tp ? <div className="text-[0.5rem] sm:text-[0.58rem] text-ink-muted/40 tabular-nums">{fmt(row.converted_tp, row.converted_tp >= 10000 ? 1 : 2)}</div> : null}
      </td>
      <td className={`${TDM} text-right text-[0.56rem] sm:text-xs font-bold ${pc(ls)}`} style={{ backgroundColor: premiumHeatmap(ls) }}>{fmt(ls, 3, 3)}</td>
      <td className={`${TDM} text-right text-[0.56rem] sm:text-xs font-bold ${pc(sl)} table-cell`} style={{ backgroundColor: premiumHeatmap(sl) }}>{fmt(sl, 3, 3)}</td>
      <td className={`${TDM} text-right text-[0.56rem] sm:text-xs ${pc(spread)}`} style={{ backgroundColor: spreadHeatmap(spread) }}>{fmt(spread, 2, 2)} %p</td>
      <td className={`${TDM} text-right text-[0.56rem] sm:text-xs ${pc(volDiff)} table-cell`}>{volDiff != null ? Number(volDiff).toFixed(2) : "-"}</td>
      {targetIsSpot ? null : <FundingCell fi={targetFI} />}
      {originIsSpot ? null : <FundingCell fi={originFI} />}
      <td className={`${TDM} text-right text-[0.56rem] sm:text-xs text-ink-muted`}>{fmtVol(row.atp24h)}</td>
    </tr>
  );
}, (p, n) => p.row === n.row && p.expanded === n.expanded && p.favActive === n.favActive && p.loggedIn === n.loggedIn && p.targetFI === n.targetFI && p.originFI === n.originFI && p.volDiff === n.volDiff && p.targetIsSpot === n.targetIsSpot && p.originIsSpot === n.originIsSpot && p.walletData === n.walletData);

function SortBtn({ children, sortKey, current, dir, onSort, className = "", vis = "" }) {
  const active = current === sortKey;
  return (
    <th className={`sticky top-0 z-[1] px-0.5 py-2.5 sm:px-2 lg:px-3 text-[0.46rem] sm:text-[0.6rem] font-bold uppercase tracking-wider text-ink-muted/60 bg-background whitespace-nowrap ${vis} ${className}`}>
      {sortKey ? (
        <button className="inline-flex items-center gap-0.5 hover:text-ink" onClick={() => onSort(sortKey)} type="button">
          {children}
          {active ? (dir === "asc" ? <ChevronUp size={9} className="text-accent" /> : <ChevronDown size={9} className="text-accent" />) : <ChevronDown size={9} className="opacity-30" />}
        </button>
      ) : children}
    </th>
  );
}

function SkeletonRows({ colCount }) {
  return Array.from({ length: 10 }).map((_, i) => (
    <tr key={i}>{[...Array(colCount)].map((_, j) => <td key={j} className={TD}><div className="h-3.5 animate-pulse rounded bg-border/20" style={{ width: `${40+Math.random()*40}%` }} /></td>)}</tr>
  ));
}

export default function PremiumTable({ displayRows, expandedAsset, onSelectAsset, favoriteMap, loggedIn, onToggleFavorite, targetFunding, originFunding, volatilityMap, walletStatus, targetMarketCode, originMarketCode, connected, searchQuery = "", aiRecommendations = [] }) {
  const [sortKey, setSortKey] = useState("");
  const [sortDir, setSortDir] = useState("desc");
  const [page, setPage] = useState(0);
  const handleSort = useCallback((key) => {
    setSortKey((prev) => {
      if (prev !== key) { setSortDir("desc"); return key; }
      if (sortDir === "desc") { setSortDir("asc"); return key; }
      // asc → reset
      setSortDir("desc");
      return "";
    });
    setPage(0);
  }, [sortDir]);

  const targetIsSpot = targetMarketCode?.includes("SPOT");
  const originIsSpot = originMarketCode?.includes("SPOT");
  const targetEx = targetMarketCode?.split("_")[0] || "";
  const originEx = originMarketCode?.split("_")[0] || "";

  const favSet = useMemo(() => new Set(Object.keys(favoriteMap).filter(k => favoriteMap[k])), [favoriteMap]);
  const sorted = useMemo(() => doSort(displayRows, sortKey, sortDir, favSet), [displayRows, sortKey, sortDir, favSet]);
  const totalPages = Math.max(1, Math.ceil(sorted.length / PAGE_SIZE));
  const sp = Math.min(page, totalPages - 1);
  const pageRows = sorted.slice(sp * PAGE_SIZE, (sp + 1) * PAGE_SIZE);
  let colCount = 8;
  if (!targetIsSpot) colCount++;
  if (!originIsSpot) colCount++;

  return (
    <div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b-2 border-border/60">
              <SortBtn vis="table-cell" className="w-[30px]" />
              <SortBtn className="text-left w-[90px]" sortKey="asset" current={sortKey} dir={sortDir} onSort={handleSort}>자산</SortBtn>
              <SortBtn vis="table-cell" className="text-center w-[40px]">전송</SortBtn>
              <SortBtn className="text-right w-[100px]" sortKey="price" current={sortKey} dir={sortDir} onSort={handleSort}>현재가</SortBtn>
              <SortBtn className="text-right" sortKey="enter" current={sortKey} dir={sortDir} onSort={handleSort}>진입김프</SortBtn>
              <SortBtn vis="table-cell" className="text-right" sortKey="exit" current={sortKey} dir={sortDir} onSort={handleSort}>탈출김프</SortBtn>
              <SortBtn className="text-right" sortKey="spread" current={sortKey} dir={sortDir} onSort={handleSort}>스프레드</SortBtn>
              <SortBtn vis="table-cell" className="text-right">변동성</SortBtn>
              {!targetIsSpot && <SortBtn vis="table-cell" className="text-right"><span className="inline-flex items-center gap-1">펀딩률 <ExIcon exchange={targetEx} size={12} /></span></SortBtn>}
              {!originIsSpot && <SortBtn vis="table-cell" className="text-right"><span className="inline-flex items-center gap-1">펀딩률 <ExIcon exchange={originEx} size={12} /></span></SortBtn>}
              <SortBtn className="text-right w-[80px]" sortKey="volume" current={sortKey} dir={sortDir} onSort={handleSort}>거래액(일)</SortBtn>
            </tr>
          </thead>
          <tbody className="divide-y divide-border/20">
            {pageRows.length ? pageRows.map(row => {
              const asset = row.base_asset;
              const tfi = targetFunding?.[asset]?.[0];
              const ofi = originFunding?.[asset]?.[0];
              const vi = volatilityMap?.[asset];
              return (
                <Fragment key={asset}>
                  <Row asset={asset} row={row} expanded={expandedAsset === asset} favActive={Boolean(favoriteMap[asset])} loggedIn={loggedIn} onSelect={onSelectAsset} onFav={onToggleFavorite} targetFI={tfi} originFI={ofi} volDiff={vi?.mean_diff} targetIsSpot={targetIsSpot} originIsSpot={originIsSpot} walletData={walletStatus?.[asset]} targetMC={targetMarketCode} originMC={originMarketCode} />
                  {expandedAsset === asset && <tr><td colSpan="99" className="p-0"><PremiumChartPanel asset={asset} originFunding={ofi} originMarketCode={originMarketCode} row={row} targetFunding={tfi} targetMarketCode={targetMarketCode} walletNetworks={walletStatus?.[asset] || {}} /></td></tr>}
                </Fragment>
              );
            }) : connected ? <SkeletonRows colCount={colCount} /> : (
              <tr><td colSpan="99" className="py-16 text-center text-sm text-ink-muted">실시간 프리미엄 데이터를 불러오는 중입니다...</td></tr>
            )}
          </tbody>
        </table>
      </div>
      {totalPages > 1 && (
        <div className="mt-3 flex items-center justify-between">
          <span className="text-xs text-ink-muted">{sorted.length}개 중 {sp*PAGE_SIZE+1}–{Math.min((sp+1)*PAGE_SIZE, sorted.length)}</span>
          <div className="flex items-center gap-1">
            <button className="rounded px-2 py-1 text-xs text-ink-muted hover:bg-surface-elevated disabled:opacity-30" disabled={sp===0} onClick={() => setPage(p => p-1)} type="button">이전</button>
            {Array.from({length:totalPages}).map((_,i) => <button key={i} className={`rounded px-2 py-1 text-xs ${i===sp?"bg-accent/20 text-accent":"text-ink-muted hover:bg-surface-elevated"}`} onClick={() => setPage(i)} type="button">{i+1}</button>)}
            <button className="rounded px-2 py-1 text-xs text-ink-muted hover:bg-surface-elevated disabled:opacity-30" disabled={sp>=totalPages-1} onClick={() => setPage(p => p+1)} type="button">다음</button>
          </div>
        </div>
      )}
    </div>
  );
}
