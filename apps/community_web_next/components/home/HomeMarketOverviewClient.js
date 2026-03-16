"use client";

import { useDeferredValue, useEffect, useMemo, useState } from "react";
import { Search } from "lucide-react";

import { useAuth } from "../auth/AuthProvider";
import { fetchCachedJson } from "../../lib/clientCache";
import MarketCombinationPicker from "./MarketCombinationPicker";
import MarketSummaryBar from "./MarketSummaryBar";
import PremiumTable from "./PremiumTable";
import AiRankPanel from "./AiRankPanel";
import FundingDiffPanel from "./FundingDiffPanel";
import useKlineWebSocket from "./hooks/useKlineWebSocket";
import useMarketData from "./hooks/useMarketData";

export default function HomeMarketOverviewClient() {
  const { authorizedListRequest, authorizedRequest, loggedIn } = useAuth();
  const [marketCodes, setMarketCodes] = useState({});
  const [statuses, setStatuses] = useState([]);
  const [targetMarketCode, setTargetMarketCode] = useState("");
  const [originMarketCode, setOriginMarketCode] = useState("");
  const [search, setSearch] = useState("");

  const deferredSearch = useDeferredValue(search);

  const originOptions = useMemo(
    () => marketCodes?.[targetMarketCode] || [],
    [marketCodes, targetMarketCode]
  );

  const effectiveOriginMarketCode = useMemo(() => {
    if (!originOptions.length) return "";
    if (originOptions.includes(originMarketCode)) return originMarketCode;
    return originOptions[0];
  }, [originMarketCode, originOptions]);

  useEffect(() => {
    let active = true;
    async function loadBaseData() {
      try {
        const [marketCodesPayload, statusesPayload] = await Promise.all([
          fetchCachedJson("/api/infocore/market-codes/", { ttlMs: 300000 }),
          fetchCachedJson("/api/exchange-status/server-status/", { ttlMs: 30000 }),
        ]);
        if (!active) return;
        setMarketCodes(marketCodesPayload || {});
        const targetCodes = Object.keys(marketCodesPayload || {});
        setTargetMarketCode(targetCodes[0] || "");
        setOriginMarketCode(marketCodesPayload?.[targetCodes[0]]?.[0] || "");
        setStatuses(statusesPayload?.results || statusesPayload || []);
      } catch {}
    }
    loadBaseData();
    return () => { active = false; };
  }, []);

  const { liveRows, connected, lastReceivedAt } = useKlineWebSocket(targetMarketCode, effectiveOriginMarketCode);
  const [expandedAsset, setExpandedAsset] = useState("");

  const filteredRows = useMemo(() => {
    const q = deferredSearch.trim().toLowerCase();
    return liveRows.filter((item) => (q ? item.base_asset?.toLowerCase().includes(q) : true));
  }, [deferredSearch, liveRows]);

  const detailSymbols = useMemo(
    () => filteredRows.slice(0, 60).map((item) => item.base_asset).filter(Boolean),
    [filteredRows]
  );

  const {
    fundingDiff, aiRecommendations, volatilityMap,
    targetFunding, originFunding, walletStatus,
    favoriteAssets, favoriteMap, toggleFavorite,
  } = useMarketData({
    targetMarketCode, originMarketCode: effectiveOriginMarketCode,
    symbolList: detailSymbols, loggedIn, authorizedListRequest, authorizedRequest,
  });

  const maintenanceItems = useMemo(
    () => statuses.filter((item) =>
      item.server_check && (item.market_code === targetMarketCode || item.market_code === effectiveOriginMarketCode)
    ),
    [effectiveOriginMarketCode, statuses, targetMarketCode]
  );

  const displayRows = useMemo(() => {
    const favoriteSymbols = new Set(favoriteAssets.map((item) => item.base_asset));
    const items = [...filteredRows];
    items.sort((left, right) => {
      const leftFav = favoriteSymbols.has(left.base_asset);
      const rightFav = favoriteSymbols.has(right.base_asset);
      if (leftFav && !rightFav) return -1;
      if (!leftFav && rightFav) return 1;
      return Number(right.atp24h || 0) - Number(left.atp24h || 0);
    });
    return items;
  }, [favoriteAssets, filteredRows]);

  const visibleExpandedAsset = useMemo(() => {
    if (!expandedAsset) return "";
    return displayRows.some((row) => row.base_asset === expandedAsset) ? expandedAsset : "";
  }, [displayRows, expandedAsset]);

  return (
    <div className="grid gap-5">
      {/* Ticker bar */}
      <MarketSummaryBar liveRows={liveRows} connected={connected} lastReceivedAt={lastReceivedAt} volatilityMap={volatilityMap} />

      {/* Market picker + search — single row */}
      <div className="flex flex-wrap items-center gap-3">
        <MarketCombinationPicker
          marketCodes={marketCodes}
          onOriginChange={setOriginMarketCode}
          onTargetChange={setTargetMarketCode}
          originMarketCode={effectiveOriginMarketCode}
          targetMarketCode={targetMarketCode}
        />
        <div className="w-full sm:w-auto sm:ml-auto flex items-center gap-2">
          <div className="relative w-full sm:w-auto">
            <Search className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 text-ink-muted/60" size={14} />
            <input
              className="w-full sm:w-[180px] rounded-lg border border-border bg-background/80 py-1.5 pl-8 pr-3 text-sm text-ink placeholder:text-ink-muted/50 outline-none transition-colors focus:border-accent/40"
              onChange={(e) => setSearch(e.target.value)}
              placeholder="검색"
              value={search}
            />
          </div>
        </div>
      </div>

      {/* Maintenance alert */}
      {maintenanceItems.length > 0 && (
        <div className="rounded-lg bg-amber-900/20 px-4 py-2.5 text-sm text-amber-300">
          {maintenanceItems.map((item) => (
            <div key={item.id}><strong>{item.market_code}</strong>: {item.message || "점검 중"}</div>
          ))}
        </div>
      )}

      {/* Premium table — the hero */}
      <PremiumTable
        displayRows={displayRows}
        expandedAsset={visibleExpandedAsset}
        onSelectAsset={(next) => setExpandedAsset((cur) => (cur === next ? "" : next))}
        favoriteMap={favoriteMap}
        loggedIn={loggedIn}
        onToggleFavorite={(symbol) => toggleFavorite(symbol).catch(() => {})}
        targetFunding={targetFunding}
        originFunding={originFunding}
        volatilityMap={volatilityMap}
        walletStatus={walletStatus}
        targetMarketCode={targetMarketCode}
        originMarketCode={effectiveOriginMarketCode}
        connected={connected}
        searchQuery={deferredSearch}
        aiRecommendations={aiRecommendations}
      />

      {/* AI + Funding — secondary panels */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <AiRankPanel recommendations={aiRecommendations} />
        <FundingDiffPanel fundingDiff={fundingDiff} />
      </div>
    </div>
  );
}
