"use client";

import { useDeferredValue, useEffect, useMemo, useState } from "react";

import { useAuth } from "../auth/AuthProvider";
import { fetchCachedJson } from "../../lib/clientCache";
import SurfaceNotice from "../ui/SurfaceNotice";

function formatNumber(value, maximumFractionDigits = 2, minimumFractionDigits = 0) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }

  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits,
    minimumFractionDigits,
  }).format(Number(value));
}

function formatPercent(value) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }

  return `${Number(value).toFixed(4)}%`;
}

function formatVolatility(value) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }

  return Number(value).toFixed(3);
}

function formatShortVolume(value) {
  const numberValue = Number(value || 0);

  if (!Number.isFinite(numberValue)) {
    return "-";
  }

  if (Math.abs(numberValue) >= 1_000_000_000) {
    return `${(numberValue / 1_000_000_000).toFixed(2)}B`;
  }

  if (Math.abs(numberValue) >= 1_000_000) {
    return `${(numberValue / 1_000_000).toFixed(2)}M`;
  }

  if (Math.abs(numberValue) >= 1_000) {
    return `${(numberValue / 1_000).toFixed(1)}K`;
  }

  return formatNumber(numberValue, 2, 0);
}

function prettifyMarketCode(code) {
  return code?.replaceAll("_", " ") || "";
}

function hasTransferRoute(walletStatus, targetMarketCode, originMarketCode, asset) {
  const assetStatus = walletStatus?.[asset];
  if (!assetStatus) {
    return false;
  }

  const targetExchange = targetMarketCode.split("_")[0];
  const originExchange = originMarketCode.split("_")[0];

  const withdrawNetworks = assetStatus?.[targetExchange]?.withdraw || [];
  const depositNetworks = assetStatus?.[originExchange]?.deposit || [];

  return withdrawNetworks.some((network) => depositNetworks.includes(network));
}

export default function HomeMarketOverviewClient() {
  const { authorizedListRequest, authorizedRequest, loggedIn } = useAuth();
  const [marketCodes, setMarketCodes] = useState({});
  const [statuses, setStatuses] = useState([]);
  const [targetMarketCode, setTargetMarketCode] = useState("");
  const [originMarketCode, setOriginMarketCode] = useState("");
  const [fundingDiff, setFundingDiff] = useState([]);
  const [aiRecommendations, setAiRecommendations] = useState([]);
  const [favoriteAssets, setFavoriteAssets] = useState([]);
  const [search, setSearch] = useState("");
  const [volatility, setVolatility] = useState([]);
  const [targetFunding, setTargetFunding] = useState({});
  const [originFunding, setOriginFunding] = useState({});
  const [walletStatus, setWalletStatus] = useState({});
  const [liveRows, setLiveRows] = useState({});
  const [realtimePairKey, setRealtimePairKey] = useState("");
  const [realtimeConnected, setRealtimeConnected] = useState(false);
  const [realtimeError, setRealtimeError] = useState("");
  const [lastRealtimeAt, setLastRealtimeAt] = useState(null);
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

  const currentPairKey = useMemo(
    () =>
      targetMarketCode && effectiveOriginMarketCode
        ? `${targetMarketCode}:${effectiveOriginMarketCode}`
        : "",
    [effectiveOriginMarketCode, targetMarketCode]
  );

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

  useEffect(() => {
    if (!currentPairKey) {
      return;
    }

    let socket = null;
    let reconnectTimer = null;
    let flushTimer = null;
    let active = true;
    const pendingRows = new Map();

    const wsBase = (
      process.env.NEXT_PUBLIC_DRF_WS_URL ||
      process.env.NEXT_PUBLIC_DRF_URL?.replace(/^http/i, "ws") ||
      window.location.origin.replace(/^http/i, "ws")
    ).replace(/\/$/, "");

    const url = new URL(`${wsBase}/kline/`);
    url.searchParams.set("target_market_code", targetMarketCode);
    url.searchParams.set("origin_market_code", effectiveOriginMarketCode);
    url.searchParams.set("interval", "1T");

    const flushPendingRows = () => {
      if (!pendingRows.size) {
        flushTimer = null;
        return;
      }

      setLiveRows((current) => {
        const next = { ...current };
        pendingRows.forEach((item, key) => {
          next[key] = item;
        });
        return next;
      });

      pendingRows.clear();
      flushTimer = null;
    };

    const connect = () => {
      socket = new WebSocket(url.toString());

      socket.addEventListener("open", () => {
        setRealtimePairKey(currentPairKey);
        setRealtimeConnected(true);
        setRealtimeError("");
      });

      socket.addEventListener("message", (event) => {
        const message = JSON.parse(event.data);

        if (message.type !== "publish") {
          return;
        }

        try {
          const result = JSON.parse(message.result);
          if (!Array.isArray(result)) {
            return;
          }

          result.forEach((item) => {
            if (item?.base_asset) {
              pendingRows.set(item.base_asset, item);
            }
          });

          setLastRealtimeAt(Date.now());

          if (!flushTimer) {
            flushTimer = window.setTimeout(flushPendingRows, 100);
          }
        } catch {
          // Ignore malformed realtime payloads.
        }
      });

      socket.addEventListener("error", () => {
        setRealtimeConnected(false);
        setRealtimeError("실시간 프리미엄 연결이 불안정합니다.");
      });

      socket.addEventListener("close", () => {
        setRealtimeConnected(false);

        if (!active) {
          return;
        }

        reconnectTimer = window.setTimeout(connect, 1500);
      });
    };

    connect();

    return () => {
      active = false;
      if (flushTimer) {
        window.clearTimeout(flushTimer);
      }
      if (reconnectTimer) {
        window.clearTimeout(reconnectTimer);
      }
      if (socket) {
        socket.close();
      }
    };
  }, [currentPairKey, effectiveOriginMarketCode, targetMarketCode]);

  const realTimeDataList = useMemo(
    () =>
      Object.values(currentPairKey === realtimePairKey ? liveRows : {}).sort(
        (left, right) => Number(right.atp24h || 0) - Number(left.atp24h || 0)
      ),
    [currentPairKey, liveRows, realtimePairKey]
  );

  const filteredRows = useMemo(() => {
    const normalizedQuery = deferredSearch.trim().toLowerCase();

    return realTimeDataList.filter((item) =>
      normalizedQuery ? item.base_asset?.toLowerCase().includes(normalizedQuery) : true
    );
  }, [deferredSearch, realTimeDataList]);

  useEffect(() => {
    let active = true;

    async function loadDerivedData() {
      if (!targetMarketCode || !effectiveOriginMarketCode) {
        return;
      }

      try {
        const [fundingDiffPayload, aiPayload] = await Promise.all([
          fetchCachedJson(
            `/api/infocore/funding-rate/diff/?market_code_x=${encodeURIComponent(
              targetMarketCode
            )}&market_code_y=${encodeURIComponent(effectiveOriginMarketCode)}`,
            { ttlMs: 15000 }
          ),
          fetchCachedJson(
            `/api/infocore/ai-rank-recommendation/?target_market_code=${encodeURIComponent(
              targetMarketCode
            )}&origin_market_code=${encodeURIComponent(effectiveOriginMarketCode)}`,
            { ttlMs: 30000 }
          ),
        ]);

        if (!active) {
          return;
        }

        setFundingDiff(fundingDiffPayload || []);
        setAiRecommendations(aiPayload || []);
      } catch {
        if (!active) {
          return;
        }

        setFundingDiff([]);
        setAiRecommendations([]);
      }
    }

    loadDerivedData();

    return () => {
      active = false;
    };
  }, [effectiveOriginMarketCode, targetMarketCode]);

  const detailSymbols = useMemo(
    () => filteredRows.slice(0, 60).map((item) => item.base_asset).filter(Boolean),
    [filteredRows]
  );

  useEffect(() => {
    let active = true;

    async function loadAssetDetails() {
      if (!targetMarketCode || !effectiveOriginMarketCode || detailSymbols.length === 0) {
        setVolatility([]);
        setTargetFunding({});
        setOriginFunding({});
        setWalletStatus({});
        return;
      }

      const assetParams = new URLSearchParams();
      detailSymbols.forEach((symbol) => assetParams.append("base_asset", symbol));
      assetParams.set("target_market_code", targetMarketCode);
      assetParams.set("origin_market_code", effectiveOriginMarketCode);
      assetParams.set("tz", "Asia/Seoul");

      const targetFundingParams = new URLSearchParams();
      detailSymbols.forEach((symbol) => targetFundingParams.append("base_asset", symbol));
      targetFundingParams.set("market_code", targetMarketCode);
      targetFundingParams.set("last_n", "1");
      targetFundingParams.set("tz", "Asia/Seoul");

      const originFundingParams = new URLSearchParams();
      detailSymbols.forEach((symbol) => originFundingParams.append("base_asset", symbol));
      originFundingParams.set("market_code", effectiveOriginMarketCode);
      originFundingParams.set("last_n", "1");
      originFundingParams.set("tz", "Asia/Seoul");

      try {
        const [volatilityPayload, targetFundingPayload, originFundingPayload, walletStatusPayload] =
          await Promise.all([
            fetchCachedJson(`/api/infocore/kline-volatility/?${assetParams.toString()}`, {
              ttlMs: 30000,
            }),
            fetchCachedJson(`/api/infocore/funding-rate/?${targetFundingParams.toString()}`, {
              ttlMs: 15000,
            }),
            fetchCachedJson(`/api/infocore/funding-rate/?${originFundingParams.toString()}`, {
              ttlMs: 15000,
            }),
            fetchCachedJson(`/api/infocore/wallet-status/?${assetParams.toString()}`, {
              ttlMs: 30000,
            }),
          ]);

        if (!active) {
          return;
        }

        setVolatility(volatilityPayload || []);
        setTargetFunding(targetFundingPayload || {});
        setOriginFunding(originFundingPayload || {});
        setWalletStatus(walletStatusPayload || {});
      } catch {
        if (!active) {
          return;
        }

        setVolatility([]);
        setTargetFunding({});
        setOriginFunding({});
        setWalletStatus({});
      }
    }

    loadAssetDetails();

    return () => {
      active = false;
    };
  }, [detailSymbols, effectiveOriginMarketCode, targetMarketCode]);

  useEffect(() => {
    let active = true;

    async function loadFavorites() {
      if (!loggedIn || !targetMarketCode || !effectiveOriginMarketCode) {
        setFavoriteAssets([]);
        return;
      }

      try {
        const payload = await authorizedListRequest(
          `/users/favorite-assets/?market_codes=${encodeURIComponent(
            targetMarketCode
          )}&market_codes=${encodeURIComponent(effectiveOriginMarketCode)}`
        );

        if (!active) {
          return;
        }

        setFavoriteAssets(payload);
      } catch {
        if (active) {
          setFavoriteAssets([]);
        }
      }
    }

    loadFavorites();

    return () => {
      active = false;
    };
  }, [authorizedListRequest, effectiveOriginMarketCode, loggedIn, targetMarketCode]);

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

  const volatilityMap = useMemo(
    () =>
      volatility.reduce((accumulator, item) => {
        accumulator[item.base_asset] = item;
        return accumulator;
      }, {}),
    [volatility]
  );

  const favoriteMap = useMemo(
    () =>
      favoriteAssets.reduce((accumulator, item) => {
        accumulator[item.base_asset] = item.id;
        return accumulator;
      }, {}),
    [favoriteAssets]
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

    return items.slice(0, 60);
  }, [favoriteAssets, filteredRows]);

  async function toggleFavorite(symbol) {
    if (!loggedIn) {
      return;
    }

    try {
      const favoriteId = favoriteMap[symbol];

      if (favoriteId) {
        await authorizedRequest(`/users/favorite-assets/${favoriteId}/`, {
          method: "DELETE",
        });
      } else {
        await authorizedRequest("/users/favorite-assets/", {
          method: "POST",
          body: {
            base_asset: symbol,
            market_codes: [targetMarketCode, effectiveOriginMarketCode],
          },
        });
      }

      const payload = await authorizedListRequest(
        `/users/favorite-assets/?market_codes=${encodeURIComponent(
          targetMarketCode
        )}&market_codes=${encodeURIComponent(effectiveOriginMarketCode)}`
      );
      setFavoriteAssets(payload);
    } catch (requestError) {
      setPageError(requestError.message || "즐겨찾기 업데이트에 실패했습니다.");
    }
  }

  return (
    <div className="section-stack">
      <section className="surface-card">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Live Premium Table</p>
            <h2>실시간 프리미엄 테이블</h2>
          </div>
          <span className="auth-chip">{displayRows.length} assets</span>
        </div>

        <div className="home-selector-grid">
          <select
            className="select-input"
            onChange={(event) => setTargetMarketCode(event.target.value)}
            value={targetMarketCode}
          >
            {Object.keys(marketCodes).map((marketCode) => (
              <option key={marketCode} value={marketCode}>
                {prettifyMarketCode(marketCode)}
              </option>
            ))}
          </select>
          <select
            className="select-input"
            onChange={(event) => setOriginMarketCode(event.target.value)}
            value={effectiveOriginMarketCode}
          >
            {originOptions.map((marketCode) => (
              <option key={marketCode} value={marketCode}>
                {prettifyMarketCode(marketCode)}
              </option>
            ))}
          </select>
        </div>

        <div className="news-filter-bar">
          <input
            className="auth-form__input"
            onChange={(event) => setSearch(event.target.value)}
            placeholder="자산 검색"
            value={search}
          />
        </div>

        <SurfaceNotice
          description={
            currentPairKey === realtimePairKey && realtimeConnected
              ? `실시간 연결 중${lastRealtimeAt ? ` · 마지막 수신 ${new Date(lastRealtimeAt).toLocaleTimeString()}` : ""}`
              : realtimeError || "실시간 프리미엄 연결을 준비 중입니다."
          }
          title={currentPairKey === realtimePairKey && realtimeConnected ? "WebSocket 연결 정상" : "WebSocket 연결 확인"}
          variant={currentPairKey === realtimePairKey && realtimeConnected ? "info" : "loading"}
        />

        {maintenanceItems.length ? (
          <div className="maintenance-banner">
            {maintenanceItems.map((item) => (
              <div key={item.id}>
                <strong>{item.market_code}</strong>: {item.message || "점검 중"}
              </div>
            ))}
          </div>
        ) : null}

        <div className="table-shell">
          <table className="data-table">
            <thead>
              <tr>
                <th>Fav</th>
                <th>Asset</th>
                <th>현재가</th>
                <th>진입 김프</th>
                <th>탈출 김프</th>
                <th>스프레드</th>
                <th>변동성</th>
                <th>타겟 펀딩</th>
                <th>오리진 펀딩</th>
                <th>전송</th>
                <th>거래액(24h)</th>
              </tr>
            </thead>
            <tbody>
              {displayRows.length ? (
                displayRows.map((row) => {
                  const asset = row.base_asset;
                  const targetFundingItem = targetFunding?.[asset]?.[0];
                  const originFundingItem = originFunding?.[asset]?.[0];
                  const volatilityItem = volatilityMap?.[asset];
                  const transferAvailable = hasTransferRoute(
                    walletStatus,
                    targetMarketCode,
                    effectiveOriginMarketCode,
                    asset
                  );
                  const spread = Number(row.SL_close || 0) - Number(row.LS_close || 0);

                  return (
                    <tr key={asset}>
                      <td>
                        <button
                          className={`favorite-button${favoriteMap[asset] ? " favorite-button--active" : ""}`}
                          disabled={!loggedIn}
                          onClick={() => toggleFavorite(asset)}
                          type="button"
                        >
                          ★
                        </button>
                      </td>
                      <td>{asset}</td>
                      <td>
                        <div>{formatNumber(row.tp, 1)}</div>
                        <small className="muted-copy">
                          {row.scr > 0 ? "+" : ""}
                          {formatNumber(row.scr, 2, 2)}%
                        </small>
                      </td>
                      <td>{formatNumber(row.LS_close, 3, 2)}</td>
                      <td>{formatNumber(row.SL_close, 3, 2)}</td>
                      <td>
                        {spread > 0 ? "+" : ""}
                        {formatNumber(spread, 2, 1)}%p
                      </td>
                      <td>{formatVolatility(volatilityItem?.mean_diff)}</td>
                      <td>{formatPercent(targetFundingItem?.funding_rate)}</td>
                      <td>{formatPercent(originFundingItem?.funding_rate)}</td>
                      <td>{transferAvailable ? "가능" : "-"}</td>
                      <td>{formatShortVolume(row.atp24h)}</td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan="11">실시간 프리미엄 데이터가 아직 없습니다.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      <div className="two-column-grid">
        <section className="surface-card">
          <div className="section-heading">
            <div>
              <p className="eyebrow">AI Rank</p>
              <h2>추천 자산</h2>
            </div>
          </div>
          <div className="stacked-list">
            {aiRecommendations.length ? (
              aiRecommendations.map((item) => (
                <article key={`${item.base_asset}-${item.rank}`} className="stacked-list__item">
                  <div className="content-list__meta">
                    <span>Rank #{item.rank}</span>
                    <span>Risk {item.risk_level}</span>
                  </div>
                  <h2>{item.base_asset}</h2>
                  <p>{item.explanation}</p>
                </article>
              ))
            ) : (
              <div className="empty-state">추천 데이터가 없습니다.</div>
            )}
          </div>
        </section>

        <section className="surface-card">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Funding Diff</p>
              <h2>펀딩비 차이</h2>
            </div>
          </div>
          <div className="table-shell">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Base Asset</th>
                  <th>Funding X</th>
                  <th>Funding Y</th>
                  <th>Diff</th>
                </tr>
              </thead>
              <tbody>
                {fundingDiff.length ? (
                  fundingDiff.map((item, index) => (
                    <tr key={`${item.base_asset}-${index}`}>
                      <td>{item.base_asset}</td>
                      <td>{formatPercent(item.funding_rate_x)}</td>
                      <td>{formatPercent(item.funding_rate_y)}</td>
                      <td>{formatPercent(item.funding_rate_diff)}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="4">표시할 펀딩 차이 데이터가 없습니다.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>
      </div>

      {pageError ? <SurfaceNotice description={pageError} variant="error" /> : null}
    </div>
  );
}
