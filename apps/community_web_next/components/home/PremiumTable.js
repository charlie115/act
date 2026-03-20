"use client";

import { Fragment, memo, useCallback, useEffect, useMemo, useState } from "react";
import { ChevronDown, ChevronRight, ChevronUp } from "lucide-react";

import { premiumHeatmap, spreadHeatmap } from "../../lib/heatmap";
import PremiumChartPanel from "./PremiumChartPanel";

const EMPTY_OBJ = {};
const MINIO_BASE = process.env.NEXT_PUBLIC_MINIO_URL || "http://localhost:19000";
const ASSET_ICON_PATH = `${MINIO_BASE}/community-media/assets/icons`;

function AssetIcon({ symbol, size = 14 }) {
  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img alt={symbol} className="rounded-full" height={size} width={size}
      loading="lazy"
      src={`${ASSET_ICON_PATH}/${symbol}.PNG`}
      onError={(e) => { e.currentTarget.style.display = "none"; if (e.currentTarget.nextSibling) e.currentTarget.nextSibling.style.display = "flex"; }}
      style={{ objectFit: "cover" }} />
  );
}

function AssetBadge({ symbol, size = 12 }) {
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
      loading="lazy"
      className="inline rounded-sm" onError={(e) => { e.currentTarget.style.display = "none"; }} />
  );
}

const PAGE_SIZE = 50;
function fmt(v, d = 2, m = 0) { if (v == null || v === "") return "-"; return new Intl.NumberFormat("en-US", { maximumFractionDigits: d, minimumFractionDigits: m }).format(Number(v)); }
function fmtVol(v) { const n = Number(v || 0); if (!Number.isFinite(n)) return "-"; if (Math.abs(n) >= 1e8) return `${(n/1e8).toFixed(1)}억`; if (Math.abs(n) >= 1e4) return `${(n/1e4).toFixed(0)}만`; return fmt(n, 0); }
function pc(v) { const n = Number(v || 0); return n > 0 ? "text-positive" : n < 0 ? "text-negative" : "text-ink-muted"; }

function premiumTextColor(value, maxAbs = 4) {
  const n = Number(value || 0);
  if (n === 0) return { color: "var(--color-ink-muted)" };
  const t = Math.min(1, Math.abs(n) / maxAbs);
  if (n > 0) {
    // Green: from white (0) to full green (maxAbs)
    const chroma = t * 0.18;
    const lightness = 0.95 - t * 0.19;
    return { color: `oklch(${lightness.toFixed(2)} ${chroma.toFixed(3)} 155)` };
  }
  // Red: from white (0) to full red (maxAbs)
  const chroma = t * 0.20;
  const lightness = 0.95 - t * 0.27;
  return { color: `oklch(${lightness.toFixed(2)} ${chroma.toFixed(3)} 25)` };
}

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

const TD = "px-0.5 py-0.5 sm:px-2 sm:py-1.5 lg:px-3 whitespace-nowrap";
const TDM = `${TD} tabular-nums`;
const IBADGE = { 1: "bg-positive/20 text-positive", 2: "bg-accent/20 text-accent", 4: "bg-opportunity/20 text-opportunity", 8: "bg-purple-400/20 text-purple-300" };

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
  return <div className="text-[0.48rem] sm:text-[0.55rem] text-ink-muted/50 italic tabular-nums whitespace-nowrap">{h}:{String(m).padStart(2,"0")}:{String(s).padStart(2,"0")}<span className="hidden sm:inline"> 남음</span></div>;
}

function FundingCell({ fi }) {
  if (!fi) return <td className={`${TDM} text-right text-[0.5rem] sm:text-xs text-ink-muted/40`}>-</td>;
  const rate = Number(fi.funding_rate || 0);
  const pct = (rate * 100).toFixed(3);
  const intH = fi.funding_interval_hours;
  const badge = IBADGE[intH] || "bg-accent/20 text-accent";
  return (
    <td className={`${TDM} text-right text-[0.5rem] sm:text-xs`}>
      <div className="flex items-center justify-end gap-1">
        <span className={pc(rate)}>{pct}</span>
        {intH != null && <span className={`rounded px-1 py-px text-[0.45rem] sm:text-[0.5rem] font-bold leading-none ${badge}`}>{intH}h</span>}
      </div>
      {fi.funding_time && <FundingCountdown fundingTime={fi.funding_time} />}
    </td>
  );
}

function WalletCell({ walletData, targetMarketCode, originMarketCode }) {
  if (!walletData || !targetMarketCode || !originMarketCode) {
    return <td className={`${TD} text-center text-ink-muted/25 hidden sm:table-cell`}>-</td>;
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
    <td className={`${TD} text-center hidden sm:table-cell`}>
      <div className="flex flex-col items-center leading-none">
        <span className={`text-[0.55rem] sm:text-[0.7rem] ${canRight ? "text-positive" : "text-negative/40"}`}>→</span>
        <span className={`text-[0.55rem] sm:text-[0.7rem] ${canLeft ? "text-positive" : "text-negative/40"}`}>←</span>
      </div>
    </td>
  );
}

const Row = memo(function Row({ asset, row, expanded, favActive, loggedIn, onSelect, onFav, targetFI, originFI, volDiff, targetIsSpot, originIsSpot, walletData, targetMC, originMC, tetherView }) {
  const ls = Number(row.LS_close || 0), sl = Number(row.SL_close || 0), spread = sl - ls;
  const dollar = Number(row.dollar || 0);
  const showTether = tetherView && Number.isFinite(dollar) && dollar > 0;
  const lsDisplay = showTether ? dollar * (1 + ls * 0.01) : ls;
  const slDisplay = showTether ? dollar * (1 + sl * 0.01) : sl;
  return (
    <tr className={`cursor-pointer transition-colors duration-150 hover:bg-surface-elevated/60 ${expanded ? "bg-accent/8" : ""}`} onClick={() => onSelect(asset)}>
      <td className={`${TD} hidden sm:table-cell w-4`}>
        <button className={`group/star transition-all duration-200 ${favActive ? "scale-110" : "hover:scale-125 active:scale-95"} disabled:opacity-40`} disabled={!loggedIn} onClick={e => { e.stopPropagation(); onFav(asset); }} type="button">
          <svg width="14" height="14" viewBox="0 0 24 24" className={`transition-all duration-200 ${favActive ? "fill-opportunity text-opportunity drop-shadow-[0_0_4px_rgba(240,185,11,0.6)]" : "fill-none text-ink-muted/30 stroke-current group-hover/star:text-opportunity/50 group-hover/star:fill-opportunity/10"}`} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
        </button>
      </td>
      <td className={TD}>
        <div className="flex items-center gap-1.5">
          <AssetBadge symbol={asset} size={12} />
          <strong className="text-[0.62rem] sm:text-sm text-ink">{asset}</strong>
          <ChevronRight size={8} strokeWidth={2.5} className={`flex-shrink-0 text-ink-muted/40 transition-transform hidden sm:inline-block ${expanded ? "rotate-90 text-accent" : ""}`} />
        </div>
      </td>
      <WalletCell walletData={walletData} targetMarketCode={targetMC} originMarketCode={originMC} />
      <td className={`${TDM} text-right whitespace-nowrap`}>
        <div className="flex items-baseline justify-end gap-1"><span className="text-[0.62rem] sm:text-sm font-semibold text-ink">{fmt(row.tp, row.tp >= 10000 ? 0 : 1)}</span><span className={`rounded px-1 py-px text-[0.45rem] sm:text-[0.56rem] font-semibold leading-none ${Number(row.scr) >= 0 ? "bg-positive/10 text-positive" : "bg-negative/10 text-negative"}`}>{row.scr > 0 ? "+" : ""}{fmt(row.scr, 2, 2)}%</span></div>
        {row.converted_tp ? <div className="text-[0.55rem] sm:text-[0.58rem] text-ink-muted/40 tabular-nums">{fmt(row.converted_tp, row.converted_tp >= 10000 ? 1 : 2)}</div> : null}
      </td>
      {showTether ? (
        <>
          <td className={`${TDM} text-right text-[0.54rem] sm:text-xs font-bold`} style={{ backgroundColor: premiumHeatmap(ls), ...premiumTextColor(ls) }}>{fmt(lsDisplay, 1)}</td>
          <td className={`${TDM} text-right text-[0.54rem] sm:text-xs font-bold hidden sm:table-cell`} style={{ backgroundColor: premiumHeatmap(sl), ...premiumTextColor(sl) }}>{fmt(slDisplay, 1)}</td>
        </>
      ) : (
        <>
          <td className={`${TDM} text-right text-[0.54rem] sm:text-xs font-bold`} style={{ backgroundColor: premiumHeatmap(ls), ...premiumTextColor(ls) }}>{fmt(ls, 3, 3)}</td>
          <td className={`${TDM} text-right text-[0.54rem] sm:text-xs font-bold hidden sm:table-cell`} style={{ backgroundColor: premiumHeatmap(sl), ...premiumTextColor(sl) }}>{fmt(sl, 3, 3)}</td>
        </>
      )}
      <td className={`${TDM} text-right text-[0.54rem] sm:text-xs ${pc(spread)}`} style={{ backgroundColor: spreadHeatmap(spread) }}>{fmt(spread, 2, 2)} %p</td>
      <td className={`${TDM} text-right text-[0.54rem] sm:text-xs ${pc(volDiff)}`}>{volDiff != null ? Number(volDiff).toFixed(2) : "-"}</td>
      {targetIsSpot ? null : <FundingCell fi={targetFI} />}
      {originIsSpot ? null : <FundingCell fi={originFI} />}
      <td className={`${TDM} text-right text-[0.54rem] sm:text-xs text-ink-muted`}>{fmtVol(row.atp24h)}</td>
    </tr>
  );
}, (p, n) => p.row === n.row && p.expanded === n.expanded && p.favActive === n.favActive && p.loggedIn === n.loggedIn && p.targetFI === n.targetFI && p.originFI === n.originFI && p.volDiff === n.volDiff && p.targetIsSpot === n.targetIsSpot && p.originIsSpot === n.originIsSpot && p.walletData === n.walletData && p.tetherView === n.tetherView);

function SortBtn({ children, sortKey, current, dir, onSort, className = "", vis = "" }) {
  const active = current === sortKey;
  return (
    <th className={`sticky top-0 z-[1] px-0.5 py-1.5 sm:px-2 lg:px-3 text-[0.5rem] sm:text-[0.65rem] font-bold uppercase tracking-wider text-ink-muted bg-[rgba(10,16,28,0.95)] backdrop-blur-sm whitespace-nowrap ${vis} ${className}`}>
      {sortKey ? (
        <button className="inline-flex items-center gap-0.5 transition-colors duration-150 hover:text-ink" onClick={() => onSort(sortKey)} type="button">
          {children}
          {active ? (dir === "asc" ? <ChevronUp size={9} className="text-accent" /> : <ChevronDown size={9} className="text-accent" />) : <ChevronDown size={9} className="opacity-30" />}
        </button>
      ) : children}
    </th>
  );
}

function SkeletonRows({ colCount }) {
  const WIDTHS = ["45%", "70%", "55%", "80%", "60%", "40%", "65%", "50%", "75%", "55%"];
  return Array.from({ length: 8 }).map((_, i) => (
    <tr key={i} className="border-b border-border/10">
      {[...Array(colCount)].map((_, j) => (
        <td key={j} className={TD}>
          <div className="h-3 rounded-sm" style={{
            width: WIDTHS[(i * colCount + j) % WIDTHS.length],
            background: "linear-gradient(90deg, rgba(255,255,255,0.03), rgba(255,255,255,0.08), rgba(255,255,255,0.03))",
            backgroundSize: "200% 100%",
            animation: "shimmer 1.6s linear infinite",
            animationDelay: `${i * 60}ms`,
          }} />
        </td>
      ))}
    </tr>
  ));
}

export default function PremiumTable({ displayRows, expandedAsset, onSelectAsset, favoriteMap, loggedIn, onToggleFavorite, targetFunding, originFunding, volatilityMap, walletStatus, targetMarketCode, originMarketCode, connected, searchQuery = "", aiRecommendations = [], isTetherPriceView = false }) {
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
    <div className="rounded-xl border border-border/30 bg-[rgba(10,16,28,0.6)] backdrop-blur-sm overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full table-auto">
          <thead>
            <tr className="border-b border-border/40">
              <SortBtn vis="hidden sm:table-cell" className="w-4" />
              <SortBtn className="text-left" sortKey="asset" current={sortKey} dir={sortDir} onSort={handleSort}>자산</SortBtn>
              <SortBtn vis="hidden sm:table-cell" className="text-center w-4"><span className="sr-only">전송</span>⇄</SortBtn>
              <SortBtn className="text-right" sortKey="price" current={sortKey} dir={sortDir} onSort={handleSort}>현재가</SortBtn>
              <SortBtn className="text-right" sortKey="enter" current={sortKey} dir={sortDir} onSort={handleSort}>{isTetherPriceView ? "진입테더" : "진입김프"}</SortBtn>
              <SortBtn vis="hidden sm:table-cell" className="text-right" sortKey="exit" current={sortKey} dir={sortDir} onSort={handleSort}>{isTetherPriceView ? "탈출테더" : "탈출김프"}</SortBtn>
              <SortBtn className="text-right" sortKey="spread" current={sortKey} dir={sortDir} onSort={handleSort}>스프레드</SortBtn>
              <SortBtn className="text-right">변동성</SortBtn>
              {!targetIsSpot && <SortBtn className="text-right"><span className="inline-flex items-center gap-1">펀딩률 <ExIcon exchange={targetEx} size={12} /></span></SortBtn>}
              {!originIsSpot && <SortBtn className="text-right"><span className="inline-flex items-center gap-1">펀딩률 <ExIcon exchange={originEx} size={12} /></span></SortBtn>}
              <SortBtn className="text-right" sortKey="volume" current={sortKey} dir={sortDir} onSort={handleSort}>거래액(일)</SortBtn>
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
                  <Row asset={asset} row={row} expanded={expandedAsset === asset} favActive={Boolean(favoriteMap[asset])} loggedIn={loggedIn} onSelect={onSelectAsset} onFav={onToggleFavorite} targetFI={tfi} originFI={ofi} volDiff={vi?.mean_diff} targetIsSpot={targetIsSpot} originIsSpot={originIsSpot} walletData={walletStatus?.[asset]} targetMC={targetMarketCode} originMC={originMarketCode} tetherView={isTetherPriceView} />
                  {expandedAsset === asset && <tr><td colSpan="99" className="p-0"><PremiumChartPanel asset={asset} originFunding={ofi} originMarketCode={originMarketCode} row={row} targetFunding={tfi} targetMarketCode={targetMarketCode} walletNetworks={walletStatus?.[asset] ?? EMPTY_OBJ} isTetherPriceView={isTetherPriceView} /></td></tr>}
                </Fragment>
              );
            }) : connected ? <SkeletonRows colCount={colCount} /> : (
              <tr><td colSpan="99" className="py-16 text-center text-sm text-ink-muted">실시간 프리미엄 데이터를 불러오는 중입니다...</td></tr>
            )}
          </tbody>
        </table>
      </div>
      {totalPages > 1 && (
        <div className="mt-3 flex items-center justify-between px-3 pb-3">
          <span className="text-xs text-ink-muted">{sorted.length}개 중 {sp*PAGE_SIZE+1}–{Math.min((sp+1)*PAGE_SIZE, sorted.length)}</span>
          <div className="flex items-center gap-1">
            <button className="cursor-pointer rounded px-2 py-1 text-xs text-ink-muted hover:bg-surface-elevated disabled:opacity-30" disabled={sp===0} onClick={() => setPage(p => p-1)} type="button">이전</button>
            {Array.from({length:totalPages}).map((_,i) => <button key={i} className={`cursor-pointer rounded px-2 py-1 text-xs ${i===sp?"bg-accent/20 text-accent":"text-ink-muted hover:bg-surface-elevated"}`} onClick={() => setPage(i)} type="button">{i+1}</button>)}
            <button className="cursor-pointer rounded px-2 py-1 text-xs text-ink-muted hover:bg-surface-elevated disabled:opacity-30" disabled={sp>=totalPages-1} onClick={() => setPage(p => p+1)} type="button">다음</button>
          </div>
        </div>
      )}
    </div>
  );
}
