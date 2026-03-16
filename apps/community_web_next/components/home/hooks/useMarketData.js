"use client";

import { useEffect, useMemo, useState } from "react";

import { fetchCachedJson } from "../../../lib/clientCache";

export default function useMarketData({
  targetMarketCode,
  originMarketCode,
  symbolList,
  loggedIn,
  authorizedListRequest,
  authorizedRequest,
}) {
  const [fundingDiff, setFundingDiff] = useState([]);
  const [aiRecommendations, setAiRecommendations] = useState([]);
  const [volatility, setVolatility] = useState([]);
  const [targetFunding, setTargetFunding] = useState({});
  const [originFunding, setOriginFunding] = useState({});
  const [walletStatus, setWalletStatus] = useState({});
  const [favoriteAssets, setFavoriteAssets] = useState([]);

  const symbolQuery = useMemo(
    () => [...new Set(symbolList)].sort().join(","),
    [symbolList]
  );

  // Derived data: funding diff + AI recommendations
  useEffect(() => {
    let active = true;

    async function loadDerivedData() {
      if (!targetMarketCode || !originMarketCode) {
        return;
      }

      try {
        const [fundingDiffPayload, aiPayload] = await Promise.all([
          fetchCachedJson(
            `/api/infocore/funding-rate/diff/?market_code_x=${encodeURIComponent(
              targetMarketCode
            )}&market_code_y=${encodeURIComponent(originMarketCode)}`,
            { ttlMs: 15000 }
          ),
          fetchCachedJson(
            `/api/infocore/ai-rank-recommendation/?target_market_code=${encodeURIComponent(
              targetMarketCode
            )}&origin_market_code=${encodeURIComponent(originMarketCode)}`,
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
  }, [originMarketCode, targetMarketCode]);

  // Asset details: volatility, funding rates, wallet status
  useEffect(() => {
    let active = true;

    async function loadAssetDetails() {
      if (!targetMarketCode || !originMarketCode || !symbolQuery) {
        setVolatility([]);
        setTargetFunding({});
        setOriginFunding({});
        setWalletStatus({});
        return;
      }

      const assetParams = new URLSearchParams();
      assetParams.set("base_asset", symbolQuery);
      assetParams.set("target_market_code", targetMarketCode);
      assetParams.set("origin_market_code", originMarketCode);
      assetParams.set("tz", "Asia/Seoul");

      const targetFundingParams = new URLSearchParams();
      targetFundingParams.set("base_asset", symbolQuery);
      targetFundingParams.set("market_code", targetMarketCode);
      targetFundingParams.set("last_n", "1");
      targetFundingParams.set("tz", "Asia/Seoul");

      const originFundingParams = new URLSearchParams();
      originFundingParams.set("base_asset", symbolQuery);
      originFundingParams.set("market_code", originMarketCode);
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
  }, [symbolQuery, originMarketCode, targetMarketCode]);

  // Favorites
  useEffect(() => {
    let active = true;

    async function loadFavorites() {
      if (!loggedIn || !targetMarketCode || !originMarketCode) {
        setFavoriteAssets([]);
        return;
      }

      try {
        const payload = await authorizedListRequest(
          `/users/favorite-assets/?market_codes=${encodeURIComponent(
            targetMarketCode
          )}&market_codes=${encodeURIComponent(originMarketCode)}`
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
  }, [authorizedListRequest, originMarketCode, loggedIn, targetMarketCode]);

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
          market_codes: [targetMarketCode, originMarketCode],
        },
      });
    }

    const payload = await authorizedListRequest(
      `/users/favorite-assets/?market_codes=${encodeURIComponent(
        targetMarketCode
      )}&market_codes=${encodeURIComponent(originMarketCode)}`
    );
    setFavoriteAssets(payload);
  }

  return {
    fundingDiff,
    aiRecommendations,
    volatilityMap,
    targetFunding,
    originFunding,
    walletStatus,
    favoriteAssets,
    favoriteMap,
    toggleFavorite,
  };
}
