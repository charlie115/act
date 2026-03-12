"use client";

import { useDeferredValue, useEffect, useMemo, useState } from "react";

import { useAuth } from "../auth/AuthProvider";
import { fetchCachedJson } from "../../lib/clientCache";
import SurfaceNotice from "../ui/SurfaceNotice";

function formatPercent(value) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }

  return `${Number(value).toFixed(4)}%`;
}

function prettifyMarketCode(code) {
  return code?.replaceAll("_", " ") || "";
}

function formatVolatility(value) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }

  return Number(value).toFixed(3);
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
  const [assets, setAssets] = useState([]);
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

  useEffect(() => {
    let active = true;

    async function loadBaseData() {
      setPageError("");

      try {
        const [marketCodesPayload, statusesPayload, assetsPayload] = await Promise.all([
          fetchCachedJson("/api/infocore/market-codes/", { ttlMs: 300000 }),
          fetchCachedJson("/api/exchange-status/server-status/", { ttlMs: 30000 }),
          fetchCachedJson("/api/infocore/assets/", { ttlMs: 300000 }),
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
        setAssets(assetsPayload?.results || []);
      } catch (requestError) {
        if (!active) {
          return;
        }

        setPageError(requestError.message || "시장 개요를 불러오지 못했습니다.");
      }
    }

    loadBaseData();

    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    let active = true;

    async function loadDerivedData() {
      if (!targetMarketCode || !effectiveOriginMarketCode) {
        return;
      }

      setPageError("");

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
      } catch (requestError) {
        if (!active) {
          return;
        }

        setPageError(requestError.message || "시장 인사이트를 불러오지 못했습니다.");
      }
    }

    loadDerivedData();

    return () => {
      active = false;
    };
  }, [effectiveOriginMarketCode, targetMarketCode]);

  const filteredAssets = useMemo(() => {
    const normalizedQuery = deferredSearch.trim().toLowerCase();

    return assets.filter((item) =>
      normalizedQuery ? item.symbol.toLowerCase().includes(normalizedQuery) : true
    );
  }, [assets, deferredSearch]);

  const displayAssets = useMemo(() => {
    const favoriteSymbols = new Set(favoriteAssets.map((item) => item.base_asset));
    const items = [...filteredAssets];

    items.sort((left, right) => {
      const leftFav = favoriteSymbols.has(left.symbol);
      const rightFav = favoriteSymbols.has(right.symbol);

      if (leftFav && !rightFav) return -1;
      if (!leftFav && rightFav) return 1;
      return left.symbol.localeCompare(right.symbol);
    });

    return items.slice(0, 30);
  }, [favoriteAssets, filteredAssets]);

  useEffect(() => {
    let active = true;

    async function loadAssetDetails() {
      if (!targetMarketCode || !effectiveOriginMarketCode || filteredAssets.length === 0) {
        setVolatility([]);
        setTargetFunding({});
        setOriginFunding({});
        setWalletStatus({});
        return;
      }

      const assetParams = new URLSearchParams();
      filteredAssets.slice(0, 20).forEach((item) => assetParams.append("base_asset", item.symbol));
      assetParams.set("target_market_code", targetMarketCode);
      assetParams.set("origin_market_code", effectiveOriginMarketCode);
      assetParams.set("tz", "Asia/Seoul");

      const targetFundingParams = new URLSearchParams();
      filteredAssets.slice(0, 20).forEach((item) => targetFundingParams.append("base_asset", item.symbol));
      targetFundingParams.set("market_code", targetMarketCode);
      targetFundingParams.set("last_n", "1");
      targetFundingParams.set("tz", "Asia/Seoul");

      const originFundingParams = new URLSearchParams();
      filteredAssets.slice(0, 20).forEach((item) => originFundingParams.append("base_asset", item.symbol));
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
      } catch (requestError) {
        if (!active) {
          return;
        }

        setPageError(requestError.message || "자산 세부 정보를 불러오지 못했습니다.");
      }
    }

    loadAssetDetails();

    return () => {
      active = false;
    };
  }, [effectiveOriginMarketCode, filteredAssets, targetMarketCode]);

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
        if (active) setFavoriteAssets([]);
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
            <p className="eyebrow">Market Workspace</p>
            <h2>시장 조합 선택</h2>
          </div>
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
        {maintenanceItems.length ? (
          <div className="maintenance-banner">
            {maintenanceItems.map((item) => (
              <div key={item.id}>
                <strong>{item.market_code}</strong>: {item.message || "점검 중"}
              </div>
            ))}
          </div>
        ) : null}
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
                    <td colSpan="4">표시할 funding diff 데이터가 없습니다.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>
      </div>

      <section className="surface-card">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Asset Explorer</p>
            <h2>자산 요약</h2>
          </div>
        </div>
        <div className="table-shell">
          <table className="data-table">
            <thead>
              <tr>
                <th>Fav</th>
                <th>Asset</th>
                <th>Target Funding</th>
                <th>Origin Funding</th>
                <th>Volatility</th>
                <th>Transfer</th>
              </tr>
            </thead>
            <tbody>
              {displayAssets.length ? (
                displayAssets.map((asset) => {
                  const targetFundingItem = targetFunding?.[asset.symbol]?.[0];
                  const originFundingItem = originFunding?.[asset.symbol]?.[0];
                  const volatilityItem = volatilityMap?.[asset.symbol];
                  const transferAvailable = hasTransferRoute(
                    walletStatus,
                    targetMarketCode,
                    effectiveOriginMarketCode,
                    asset.symbol
                  );

                  return (
                    <tr key={asset.symbol}>
                      <td>
                        <button
                          className={`favorite-button${favoriteMap[asset.symbol] ? " favorite-button--active" : ""}`}
                          disabled={!loggedIn}
                          onClick={() => toggleFavorite(asset.symbol)}
                          type="button"
                        >
                          ★
                        </button>
                      </td>
                      <td>{asset.symbol}</td>
                      <td>{formatPercent(targetFundingItem?.funding_rate)}</td>
                      <td>{formatPercent(originFundingItem?.funding_rate)}</td>
                      <td>{formatVolatility(volatilityItem?.mean_diff)}</td>
                      <td>{transferAvailable ? "가능" : "-"}</td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan="6">표시할 자산이 없습니다.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      {pageError ? <SurfaceNotice description={pageError} variant="error" /> : null}
    </div>
  );
}
