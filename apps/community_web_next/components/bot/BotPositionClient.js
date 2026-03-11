"use client";

import { useEffect, useMemo, useState } from "react";

import { useAuth } from "../auth/AuthProvider";

function formatAmount(value, digits = 4) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }

  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: digits,
    minimumFractionDigits: 0,
  }).format(Number(value));
}

export default function BotPositionClient({ marketCodeCombination }) {
  const { authorizedRequest } = useAuth();
  const [targetData, setTargetData] = useState([]);
  const [originData, setOriginData] = useState([]);
  const [pageError, setPageError] = useState("");

  useEffect(() => {
    let active = true;

    async function loadPositions() {
      setPageError("");

      try {
        const targetPath = marketCodeCombination.target.isSpot
          ? `/tradecore/spot-position/?trade_config_uuid=${marketCodeCombination.tradeConfigUuid}&market_code=${encodeURIComponent(
              marketCodeCombination.target.value
            )}`
          : `/tradecore/futures-position/?trade_config_uuid=${marketCodeCombination.tradeConfigUuid}&market_code=${encodeURIComponent(
              marketCodeCombination.target.value
            )}`;

        const originPath = marketCodeCombination.origin.isSpot
          ? `/tradecore/spot-position/?trade_config_uuid=${marketCodeCombination.tradeConfigUuid}&market_code=${encodeURIComponent(
              marketCodeCombination.origin.value
            )}`
          : `/tradecore/futures-position/?trade_config_uuid=${marketCodeCombination.tradeConfigUuid}&market_code=${encodeURIComponent(
              marketCodeCombination.origin.value
            )}`;

        const [nextTargetData, nextOriginData] = await Promise.all([
          authorizedRequest(targetPath),
          authorizedRequest(originPath),
        ]);

        if (!active) {
          return;
        }

        setTargetData(nextTargetData || []);
        setOriginData(nextOriginData || []);
      } catch (requestError) {
        if (!active) {
          return;
        }

        setPageError(requestError.message || "Failed to load positions.");
      }
    }

    loadPositions();

    return () => {
      active = false;
    };
  }, [authorizedRequest, marketCodeCombination]);

  const rows = useMemo(() => {
    const map = new Map();

    targetData.forEach((item) => {
      const key = item.asset || item.base_asset || item.symbol;
      if (!key || key === "KRW") {
        return;
      }
      map.set(key, { asset: key, target: item });
    });

    originData.forEach((item) => {
      const key = item.asset || item.base_asset || item.symbol;
      if (!key || key === "KRW") {
        return;
      }

      const current = map.get(key) || { asset: key };
      current.origin = item;
      map.set(key, current);
    });

    return [...map.values()].sort((left, right) => left.asset.localeCompare(right.asset));
  }, [originData, targetData]);

  return (
    <section className="surface-card">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Position</p>
          <h2>현재 포지션</h2>
        </div>
      </div>
      <div className="table-shell">
        <table className="data-table">
          <thead>
            <tr>
              <th>Asset</th>
              <th>Target Position</th>
              <th>Target ROI</th>
              <th>Origin Position</th>
              <th>Origin ROI</th>
            </tr>
          </thead>
          <tbody>
            {rows.length ? (
              rows.map((row) => (
                <tr key={row.asset}>
                  <td>{row.asset}</td>
                  <td>{formatAmount(row.target?.qty ?? row.target?.free)}</td>
                  <td>{formatAmount(row.target?.ROI, 2)}</td>
                  <td>{formatAmount(row.origin?.qty ?? row.origin?.free)}</td>
                  <td>{formatAmount(row.origin?.ROI, 2)}</td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="5">No position data found.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      {pageError ? <p className="auth-card__error">{pageError}</p> : null}
    </section>
  );
}
