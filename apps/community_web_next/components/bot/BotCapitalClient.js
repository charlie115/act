"use client";

import { useEffect, useState } from "react";

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

function InfoRow({ label, targetValue, originValue }) {
  return (
    <tr>
      <td>{label}</td>
      <td>{targetValue}</td>
      <td>{originValue}</td>
    </tr>
  );
}

export default function BotCapitalClient({ marketCodeCombination }) {
  const { authorizedRequest } = useAuth();
  const [targetCapital, setTargetCapital] = useState(null);
  const [originCapital, setOriginCapital] = useState(null);
  const [dollarInfo, setDollarInfo] = useState(null);
  const [usdtInfo, setUsdtInfo] = useState(null);
  const [pageError, setPageError] = useState("");

  useEffect(() => {
    let active = true;

    async function loadCapital() {
      setPageError("");

      try {
        const [nextTargetCapital, nextOriginCapital, nextDollarInfo, nextUsdtInfo] =
          await Promise.all([
            authorizedRequest(
              `/tradecore/capital/?trade_config_uuid=${marketCodeCombination.tradeConfigUuid}&market_code=${encodeURIComponent(
                marketCodeCombination.target.value
              )}`
            ),
            authorizedRequest(
              `/tradecore/capital/?trade_config_uuid=${marketCodeCombination.tradeConfigUuid}&market_code=${encodeURIComponent(
                marketCodeCombination.origin.value
              )}`
            ),
            fetch("/api/infocore/dollar/", { cache: "no-store" }).then((response) => response.json()),
            fetch("/api/infocore/usdt/", { cache: "no-store" }).then((response) => response.json()),
          ]);

        if (!active) {
          return;
        }

        setTargetCapital(nextTargetCapital);
        setOriginCapital(nextOriginCapital);
        setDollarInfo(nextDollarInfo);
        setUsdtInfo(nextUsdtInfo);
      } catch (requestError) {
        if (!active) {
          return;
        }

        setPageError(requestError.message || "Failed to load capital.");
      }
    }

    loadCapital();

    return () => {
      active = false;
    };
  }, [authorizedRequest, marketCodeCombination]);

  const totalBeforeDollar =
    Number(targetCapital?.before_pnl || 0) +
    Number(originCapital?.before_pnl || 0) *
      (originCapital?.currency === "USDT" ? Number(dollarInfo?.price || 0) : 1);
  const totalAfterDollar =
    Number(targetCapital?.after_pnl || 0) +
    Number(originCapital?.after_pnl || 0) *
      (originCapital?.currency === "USDT" ? Number(dollarInfo?.price || 0) : 1);
  const totalBeforeUsdt =
    Number(targetCapital?.before_pnl || 0) +
    Number(originCapital?.before_pnl || 0) *
      (originCapital?.currency === "USDT" ? Number(usdtInfo?.price || 0) : 1);
  const totalAfterUsdt =
    Number(targetCapital?.after_pnl || 0) +
    Number(originCapital?.after_pnl || 0) *
      (originCapital?.currency === "USDT" ? Number(usdtInfo?.price || 0) : 1);

  return (
    <section className="surface-card">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Capital</p>
          <h2>자본 현황</h2>
        </div>
      </div>
      <div className="table-shell">
        <table className="data-table">
          <thead>
            <tr>
              <th>Metric</th>
              <th>{marketCodeCombination.target.value}</th>
              <th>{marketCodeCombination.origin.value}</th>
            </tr>
          </thead>
          <tbody>
            <InfoRow
              label="Currency"
              originValue={originCapital?.currency || "-"}
              targetValue={targetCapital?.currency || "-"}
            />
            <InfoRow
              label="Free"
              originValue={formatAmount(originCapital?.free)}
              targetValue={formatAmount(targetCapital?.free)}
            />
            <InfoRow
              label="Locked"
              originValue={formatAmount(originCapital?.locked)}
              targetValue={formatAmount(targetCapital?.locked)}
            />
            <InfoRow
              label="Before PnL"
              originValue={formatAmount(originCapital?.before_pnl)}
              targetValue={formatAmount(targetCapital?.before_pnl)}
            />
            <InfoRow
              label="PnL"
              originValue={formatAmount(originCapital?.pnl)}
              targetValue={formatAmount(targetCapital?.pnl)}
            />
            <InfoRow
              label="After PnL"
              originValue={formatAmount(originCapital?.after_pnl)}
              targetValue={formatAmount(targetCapital?.after_pnl)}
            />
            <tr>
              <td>Total before PnL (USD/KRW applied)</td>
              <td colSpan="2">{formatAmount(totalBeforeDollar)}</td>
            </tr>
            <tr>
              <td>Total after PnL (USD/KRW applied)</td>
              <td colSpan="2">{formatAmount(totalAfterDollar)}</td>
            </tr>
            <tr>
              <td>Total before PnL (USDT/KRW applied)</td>
              <td colSpan="2">{formatAmount(totalBeforeUsdt)}</td>
            </tr>
            <tr>
              <td>Total after PnL (USDT/KRW applied)</td>
              <td colSpan="2">{formatAmount(totalAfterUsdt)}</td>
            </tr>
          </tbody>
        </table>
      </div>
      {pageError ? <p className="auth-card__error">{pageError}</p> : null}
    </section>
  );
}
