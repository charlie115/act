"use client";

import { useEffect, useMemo, useState } from "react";

import ArbitrageLayout from "./ArbitrageLayout";

function formatPercent(value) {
  if (value === null || value === undefined) {
    return "-";
  }

  return `${Number(value).toFixed(4)}%`;
}

export default function ArbitrageAverageFundingRateClient() {
  const [lookback, setLookback] = useState(10);
  const [data, setData] = useState([]);
  const [pageError, setPageError] = useState("");

  useEffect(() => {
    let active = true;

    async function loadData() {
      setPageError("");

      try {
        const response = await fetch(`/api/infocore/funding-rate/average/?n=${lookback}`, {
          cache: "no-store",
        });

        if (!response.ok) {
          throw new Error("Failed to load average funding rate.");
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
  }, [lookback]);

  const rows = useMemo(
    () => [...data].sort((left, right) => Number(right.funding_rate || 0) - Number(left.funding_rate || 0)),
    [data]
  );

  return (
    <ArbitrageLayout currentTab="avg">
      <section className="surface-card">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Average Funding Rate</p>
            <h2>최근 평균 펀딩비</h2>
          </div>
          <select
            className="select-input"
            onChange={(event) => setLookback(Number(event.target.value))}
            value={lookback}
          >
            <option value="5">Last 5</option>
            <option value="10">Last 10</option>
            <option value="20">Last 20</option>
            <option value="50">Last 50</option>
          </select>
        </div>
        <div className="table-shell">
          <table className="data-table">
            <thead>
              <tr>
                <th>Base Asset</th>
                <th>Market</th>
                <th>Quote</th>
                <th>Average Funding Rate</th>
              </tr>
            </thead>
            <tbody>
              {rows.length ? (
                rows.map((item, index) => (
                  <tr key={`${item.market_code}-${item.base_asset}-${index}`}>
                    <td>{item.base_asset}</td>
                    <td>{item.market_code}</td>
                    <td>{item.quote_asset}</td>
                    <td>{formatPercent(item.funding_rate)}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="4">No average funding rate data found.</td>
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
