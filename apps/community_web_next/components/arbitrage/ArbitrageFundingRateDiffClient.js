"use client";

import { useEffect, useMemo, useState } from "react";

import ArbitrageLayout from "./ArbitrageLayout";

function formatPercent(value) {
  if (value === null || value === undefined) {
    return "-";
  }

  return `${Number(value).toFixed(4)}%`;
}

export default function ArbitrageFundingRateDiffClient() {
  const [data, setData] = useState([]);
  const [pageError, setPageError] = useState("");

  useEffect(() => {
    let active = true;

    async function loadData() {
      setPageError("");

      try {
        const response = await fetch("/api/infocore/funding-rate/diff/", {
          cache: "no-store",
        });

        if (!response.ok) {
          throw new Error("Failed to load funding rate diff.");
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

  const rows = useMemo(
    () =>
      [...data].sort(
        (left, right) =>
          Math.abs(Number(right.funding_rate_diff || 0)) -
          Math.abs(Number(left.funding_rate_diff || 0))
      ),
    [data]
  );

  return (
    <ArbitrageLayout currentTab="diff">
      <section className="surface-card">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Funding Rate Diff</p>
            <h2>거래소 간 펀딩비 차이</h2>
          </div>
        </div>
        <div className="table-shell">
          <table className="data-table">
            <thead>
              <tr>
                <th>Base Asset</th>
                <th>Market X</th>
                <th>Funding X</th>
                <th>Market Y</th>
                <th>Funding Y</th>
                <th>Diff</th>
              </tr>
            </thead>
            <tbody>
              {rows.length ? (
                rows.map((item, index) => (
                  <tr key={`${item.base_asset}-${item.market_code_x}-${item.market_code_y}-${index}`}>
                    <td>{item.base_asset}</td>
                    <td>{item.exchange_x} / {item.market_code_x}</td>
                    <td>{formatPercent(item.funding_rate_x)}</td>
                    <td>{item.exchange_y} / {item.market_code_y}</td>
                    <td>{formatPercent(item.funding_rate_y)}</td>
                    <td>{formatPercent(item.funding_rate_diff)}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="6">No funding rate diff data found.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        {pageError ? <p className="auth-card__error">{pageError}</p> : null}
      </section>
    </ArbitrageLayout>
  );
}
