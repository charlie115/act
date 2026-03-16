"use client";

import { useDeferredValue, useEffect, useMemo, useState } from "react";

import { useAuth } from "../auth/AuthProvider";
import { fetchCachedJson } from "../../lib/clientCache";
import MarketCombinationPicker from "./MarketCombinationPicker";
import MarketSummaryBar from "./MarketSummaryBar";
import PremiumTable from "./PremiumTable";
import AiRankPanel from "./AiRankPanel";
import FundingDiffPanel from "./FundingDiffPanel";
import SurfaceNotice from "../ui/SurfaceNotice";
import { TextInput } from "../ui/text-input.jsx";
import useKlineWebSocket from "./hooks/useKlineWebSocket";
import useMarketData from "./hooks/useMarketData";

function prettifyMarketCode(code) {
  return code?.replaceAll("_", " ") || "";
}

export default function HomeMarketOverviewClient() {
  const { authorizedListRequest, authorizedRequest, loggedIn } = useAuth();
  const [marketCodes, setMarketCodes] = useState({});
  const [statuses, setStatuses] = useState([]);
  const [targetMarketCode, setTargetMarketCode] = useState("");
  const [originMarketCode, setOriginMarketCode] = useState("");
  const [search, setSearch] = useState("");
  const [expandedAsset, setExpandedAsset] = useState("");
  const [pageError, setPageError] = useState("");

  const deferredSearch = useDeferredValue(search);

  const originOptions = useMemo(
    () => marketCodes?.[targetMarketCode] || [],
    [marketCodes, targetMarketCode]
  );

  const effectiveOriginMarketCode = useMemo(() => {
    if (!originOptions.length) {
      return "";
    }

    if (originOptions.includes(originMarketCode)) {
      return originMarketCode;
    }

    return originOptions[0];
  }, [originMarketCode, originOptions]);

  // Load base data: market codes + statuses
  useEffect(() => {
    let active = true;

    async function loadBaseData() {
      setPageError("");

      try {
        const [marketCodesPayload, statusesPayload] = await Promise.all([
          fetchCachedJson("/api/infocore/market-codes/", { ttlMs: 300000 }),
          fetchCachedJson("/api/exchange-status/server-status/", { ttlMs: 30000 }),
        ]);

        if (!active) {
          return;
        }

        setMarketCodes(marketCodesPayload || {});
        const targetCodes = Object.keys(marketCodesPayload || {});
        const defaultTarget = targetCodes[0] || "";
        const defaultOrigin = marketCodesPayload?.[defaultTarget]?.[0] || "";

        setTargetMarketCode(defaultTarget);
        setOriginMarketCode(defaultOrigin);
        setStatuses(statusesPayload?.results || statusesPayload || []);
      } catch (requestError) {
        if (!active) {
          return;
        }

        setPageError(requestError.message || "시장 구성을 불러오지 못했습니다.");
      }
    }

    loadBaseData();

    return () => {
      active = false;
    };
  }, []);

  // WebSocket hook
  const { liveRows, connected, error: realtimeError, lastReceivedAt } = useKlineWebSocket(
    targetMarketCode,
    effectiveOriginMarketCode
  );

  // Filter & search
  const filteredRows = useMemo(() => {
    const normalizedQuery = deferredSearch.trim().toLowerCase();

    return liveRows.filter((item) =>
      normalizedQuery ? item.base_asset?.toLowerCase().includes(normalizedQuery) : true
    );
  }, [deferredSearch, liveRows]);

  // Symbol list for detail fetches
  const detailSymbols = useMemo(
    () => filteredRows.slice(0, 60).map((item) => item.base_asset).filter(Boolean),
    [filteredRows]
  );

  // Market data hook
  const {
    fundingDiff,
    aiRecommendations,
    volatilityMap,
    targetFunding,
    originFunding,
    walletStatus,
    favoriteAssets,
    favoriteMap,
    toggleFavorite,
  } = useMarketData({
    targetMarketCode,
    originMarketCode: effectiveOriginMarketCode,
    symbolList: detailSymbols,
    loggedIn,
    authorizedListRequest,
    authorizedRequest,
  });

  // Maintenance checks
  const maintenanceItems = useMemo(
    () =>
      statuses.filter(
        (item) =>
          item.server_check &&
          (item.market_code === targetMarketCode ||
            item.market_code === effectiveOriginMarketCode)
      ),
    [effectiveOriginMarketCode, statuses, targetMarketCode]
  );

  // Display rows: favorites first, then by volume
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

  // Only show expanded asset if it's in the visible list
  const visibleExpandedAsset = useMemo(() => {
    if (!expandedAsset) {
      return "";
    }

    return displayRows.some((row) => row.base_asset === expandedAsset) ? expandedAsset : "";
  }, [displayRows, expandedAsset]);

  const selectedPairLabel = useMemo(() => {
    if (!targetMarketCode || !effectiveOriginMarketCode) {
      return "시장 조합 대기 중";
    }

    return `${prettifyMarketCode(targetMarketCode)} → ${prettifyMarketCode(effectiveOriginMarketCode)}`;
  }, [effectiveOriginMarketCode, targetMarketCode]);

  async function handleToggleFavorite(symbol) {
    try {
      await toggleFavorite(symbol);
    } catch (requestError) {
      setPageError(requestError.message || "즐겨찾기 업데이트에 실패했습니다.");
    }
  }

  return (
    <div className="grid gap-4">
      {/* Market Summary Bar */}
      <MarketSummaryBar
        liveRows={liveRows}
        connected={connected}
        lastReceivedAt={lastReceivedAt}
      />

      {/* Premium Table Section */}
      <section className="rounded-lg border border-border bg-background/92 p-4">
        <div className="mb-3 flex items-end justify-between gap-3">
          <div>
            <p className="mb-1.5 text-[0.66rem] font-bold uppercase tracking-[0.14em] text-accent">Live Premium Table</p>
            <h2 className="text-xl font-bold leading-tight text-ink">실시간 프리미엄 테이블</h2>
          </div>
          <span className="rounded-lg border border-border bg-background/70 px-3 py-1.5 text-xs font-semibold text-ink-muted">
            {displayRows.length}개 자산
          </span>
        </div>

        <div className="mb-3 grid gap-2.5">
          <MarketCombinationPicker
            marketCodes={marketCodes}
            onOriginChange={setOriginMarketCode}
            onTargetChange={setTargetMarketCode}
            originMarketCode={effectiveOriginMarketCode}
            targetMarketCode={targetMarketCode}
          />
          <div className="justify-self-end" style={{ width: "min(320px, 100%)" }}>
            <TextInput
              label="자산 검색"
              onChange={(event) => setSearch(event.target.value)}
              placeholder="자산 검색"
              value={search}
            />
          </div>
        </div>

        {/* Status strip */}
        <div className="mb-3 grid grid-cols-4 gap-px overflow-hidden rounded-lg border border-border bg-border">
          <div className="flex flex-col gap-1 bg-background/96 px-3 py-2">
            <span className="text-[0.56rem] font-bold uppercase tracking-[0.14em] text-accent">선택 조합</span>
            <strong className="text-xs font-bold text-ink">{selectedPairLabel}</strong>
          </div>
          <div className="flex flex-col gap-1 bg-background/96 px-3 py-2">
            <span className="text-[0.56rem] font-bold uppercase tracking-[0.14em] text-accent">실시간 상태</span>
            <strong className="text-xs font-bold text-ink">{connected ? "연결됨" : "재연결 중"}</strong>
          </div>
          <div className="flex flex-col gap-1 bg-background/96 px-3 py-2">
            <span className="text-[0.56rem] font-bold uppercase tracking-[0.14em] text-accent">즐겨찾기</span>
            <strong className="text-xs font-bold text-ink">{favoriteAssets.length}</strong>
          </div>
          <div className="flex flex-col gap-1 bg-background/96 px-3 py-2">
            <span className="text-[0.56rem] font-bold uppercase tracking-[0.14em] text-accent">점검</span>
            <strong className="text-xs font-bold text-ink">{maintenanceItems.length}</strong>
          </div>
        </div>

        <SurfaceNotice
          description={
            connected
              ? `실시간 연결 중${lastReceivedAt ? ` · 마지막 수신 ${new Date(lastReceivedAt).toLocaleTimeString()}` : ""}`
              : realtimeError || "실시간 프리미엄 연결을 준비 중입니다."
          }
          title={connected ? "WebSocket 연결 정상" : "WebSocket 연결 확인"}
          variant={connected ? "info" : "loading"}
        />

        {maintenanceItems.length ? (
          <div className="mt-3 grid gap-2 rounded-lg bg-amber-900/20 p-3 text-sm text-amber-300">
            {maintenanceItems.map((item) => (
              <div key={item.id}>
                <strong>{item.market_code}</strong>: {item.message || "점검 중"}
              </div>
            ))}
          </div>
        ) : null}

        <div className="mt-3">
          <PremiumTable
            displayRows={displayRows}
            expandedAsset={visibleExpandedAsset}
            onSelectAsset={(nextAsset) =>
              setExpandedAsset((current) => (current === nextAsset ? "" : nextAsset))
            }
            favoriteMap={favoriteMap}
            loggedIn={loggedIn}
            onToggleFavorite={handleToggleFavorite}
            targetFunding={targetFunding}
            originFunding={originFunding}
            volatilityMap={volatilityMap}
            walletStatus={walletStatus}
            targetMarketCode={targetMarketCode}
            originMarketCode={effectiveOriginMarketCode}
            connected={connected}
          />
        </div>
      </section>

      {/* AI Rank + Funding Diff */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <AiRankPanel recommendations={aiRecommendations} />
        <FundingDiffPanel fundingDiff={fundingDiff} />
      </div>

      {pageError ? <SurfaceNotice description={pageError} variant="error" /> : null}
    </div>
  );
}
