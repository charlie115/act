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

export default function BotPnlHistoryClient({ marketCodeCombination }) {
  const { authorizedRequest } = useAuth();
  const [data, setData] = useState([]);
  const [pageError, setPageError] = useState("");

  useEffect(() => {
    let active = true;

    async function loadHistory() {
      setPageError("");

      try {
        const payload = await authorizedRequest(
          `/tradecore/pnl-history/?trade_config_uuid=${marketCodeCombination.tradeConfigUuid}`
        );

        if (!active) {
          return;
        }

        setData(payload || []);
      } catch (requestError) {
        if (!active) {
          return;
        }

        setPageError(requestError.message || "Failed to load PnL history.");
      }
    }

    loadHistory();

    return () => {
      active = false;
    };
  }, [authorizedRequest, marketCodeCombination.tradeConfigUuid]);

  const rows = useMemo(
    () =>
      [...data].sort(
        (left, right) => new Date(right.registered_datetime) - new Date(left.registered_datetime)
      ),
    [data]
  );

  const totalPnlAfterFee = useMemo(
    () => rows.reduce((sum, item) => sum + Number(item.total_pnl_after_fee || 0), 0),
    [rows]
  );

  return (
    <div className="section-stack">
      <section className="surface-card">
        <div className="section-heading">
          <div>
            <p className="eyebrow">PnL History</p>
            <h2>실현 손익 내역</h2>
          </div>
        </div>
        <div className="table-shell">
          <table className="data-table">
            <thead>
              <tr>
                <th>Registered</th>
                <th>Trade UUID</th>
                <th>Premium Gap</th>
                <th>Total Currency</th>
                <th>Total PnL</th>
                <th>Total PnL After Fee</th>
              </tr>
            </thead>
            <tbody>
              {rows.length ? (
                rows.map((item) => (
                  <tr key={item.uuid}>
                    <td>{new Date(item.registered_datetime).toLocaleString()}</td>
                    <td className="mono-cell mono-cell--wrap">{item.trade_uuid}</td>
                    <td>{formatAmount(item.realized_premium_gap_p, 4)}</td>
                    <td>{item.total_currency}</td>
                    <td>{formatAmount(item.total_pnl)}</td>
                    <td>{formatAmount(item.total_pnl_after_fee)}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="6">No PnL history found.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      <section className="surface-card">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Summary</p>
            <h2>누적 손익</h2>
          </div>
        </div>
        <div className="inline-note">
          Total PnL after fee: <strong>{formatAmount(totalPnlAfterFee)}</strong>
        </div>
        {pageError ? <p className="auth-card__error">{pageError}</p> : null}
      </section>
    </div>
  );
}
