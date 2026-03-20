"use client";

import { useEffect, useState } from "react";
import { LayoutGrid } from "lucide-react";
import { useAuth } from "../auth/AuthProvider";
import ExchangeIcon from "../ui/ExchangeIcon";

const TH =
  "sticky top-0 z-[1] px-2 py-2 sm:px-3 text-[0.5rem] sm:text-[0.65rem] font-bold uppercase tracking-wider text-ink-muted bg-[rgba(10,16,28,0.95)] backdrop-blur-sm whitespace-nowrap";
const TD = "px-2 py-1.5 sm:px-3 sm:py-2 whitespace-nowrap";
const TDM = `${TD} tabular-nums`;

const fmt = new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 });

function fmtNum(v) {
  if (v == null || v === "") return "-";
  return fmt.format(Number(v));
}

function pnlColor(v) {
  const n = Number(v);
  if (Number.isNaN(n) || n === 0) return "text-ink";
  return n > 0 ? "text-positive" : "text-negative";
}

const PNL_ROWS = ["pnl"];

const ROWS = [
  { key: "currency", label: "화폐" },
  { key: "free", label: "가용잔고" },
  { key: "locked", label: "주문잠금" },
  { key: "before_pnl", label: "손익 전" },
  { key: "pnl", label: "손익" },
  { key: "after_pnl", label: "손익 후" },
];

export default function BotCapitalClient({ marketCodeCombination }) {
  const { authorizedRequest } = useAuth();
  const [targetData, setTargetData] = useState(null);
  const [originData, setOriginData] = useState(null);
  const [dollarRate, setDollarRate] = useState(null);
  const [usdtRate, setUsdtRate] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const configUuid =
    marketCodeCombination?.tradeConfigUuid ||
    marketCodeCombination?.trade_config_uuid;
  const targetMarket = marketCodeCombination?.target;
  const originMarket = marketCodeCombination?.origin;

  useEffect(() => {
    if (!configUuid || !targetMarket?.value || !originMarket?.value) return;
    let active = true;

    async function load() {
      setLoading(true);
      setError(false);
      try {
        const [target, origin, dollar, usdt] = await Promise.all([
          authorizedRequest(
            `/tradecore/capital/?trade_config_uuid=${configUuid}&market_code=${targetMarket.value}`,
          ),
          authorizedRequest(
            `/tradecore/capital/?trade_config_uuid=${configUuid}&market_code=${originMarket.value}`,
          ),
          authorizedRequest("/infocore/dollar/"),
          authorizedRequest("/infocore/usdt/"),
        ]);
        if (active) {
          setTargetData(target);
          setOriginData(origin);
          setDollarRate(Number(dollar?.price) || 0);
          setUsdtRate(Number(usdt?.price) || 0);
        }
      } catch {
        if (active) setError(true);
      } finally {
        if (active) setLoading(false);
      }
    }

    load();
    return () => {
      active = false;
    };
  }, [configUuid, targetMarket?.value, originMarket?.value, authorizedRequest]);

  if (loading) {
    return (
      <div className="grid place-items-center py-12">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-border border-t-accent" />
      </div>
    );
  }

  if (error || (!targetData && !originData)) {
    return (
      <div className="space-y-4 p-4">
        <h3 className="section-title">
          <LayoutGrid size={15} strokeWidth={2} className="text-accent" />
          자본 현황
        </h3>
        <p className="py-8 text-center text-sm text-ink-muted">
          자본 정보를 불러올 수 없습니다.
        </p>
      </div>
    );
  }

  // --- Aggregate calculations ---
  const tCurrency = targetData?.currency || "";
  const oCurrency = originData?.currency || "";

  const tBeforePnl = Number(targetData?.before_pnl) || 0;
  const oBeforePnl = Number(originData?.before_pnl) || 0;
  const tAfterPnl = Number(targetData?.after_pnl) || 0;
  const oAfterPnl = Number(originData?.after_pnl) || 0;

  // Target is typically USDT, origin is typically KRW
  const isTargetUsdt = tCurrency === "USDT";
  const isOriginKrw = oCurrency === "KRW";

  let totalBeforeUsd = null;
  let totalAfterUsd = null;
  let totalBeforeUsdt = null;
  let totalAfterUsdt = null;

  if (isTargetUsdt && isOriginKrw && dollarRate > 0 && usdtRate > 0) {
    totalBeforeUsd = tBeforePnl * dollarRate + oBeforePnl;
    totalAfterUsd = tAfterPnl * dollarRate + oAfterPnl;
    totalBeforeUsdt = tBeforePnl * usdtRate + oBeforePnl;
    totalAfterUsdt = tAfterPnl * usdtRate + oAfterPnl;
  }

  function renderCell(key, data) {
    if (!data) return "-";
    const val = data[key];
    if (key === "currency") {
      return (
        <span className="text-[0.72rem] font-semibold text-ink sm:text-xs">
          {val || "-"}
        </span>
      );
    }
    const isPnl = PNL_ROWS.includes(key);
    return (
      <span
        className={`text-[0.72rem] sm:text-xs ${isPnl ? pnlColor(val) : "text-ink"}`}
      >
        {fmtNum(val)}
      </span>
    );
  }

  function renderAggRow(label, value) {
    const isPnl = label.includes("손익 후");
    return (
      <tr
        key={label}
        className="transition-colors duration-150 hover:bg-surface-elevated/60"
      >
        <td className={`${TD} text-left text-[0.72rem] font-medium text-ink-muted sm:text-xs`}>
          {label}
        </td>
        <td
          className={`${TDM} text-right text-[0.72rem] sm:text-xs`}
          colSpan={2}
        >
          <span className={isPnl ? pnlColor(value) : "text-ink"}>
            {value != null ? fmtNum(value) : "-"}
          </span>
        </td>
      </tr>
    );
  }

  return (
    <div className="space-y-4 p-4">
      <h3 className="section-title">
        <LayoutGrid size={15} strokeWidth={2} className="text-accent" />
        자본 현황
      </h3>

      <div className="rounded-lg border border-border/60 bg-background/80 backdrop-blur-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full table-auto">
            <thead>
              <tr className="border-b border-border/40">
                <th className={`${TH} text-left`}>항목</th>
                <th className={`${TH} text-right`}>
                  <span className="inline-flex items-center gap-1.5">
                    <ExchangeIcon
                      exchange={targetMarket?.exchange}
                      size={14}
                    />
                    Target
                  </span>
                </th>
                <th className={`${TH} text-right`}>
                  <span className="inline-flex items-center gap-1.5">
                    <ExchangeIcon
                      exchange={originMarket?.exchange}
                      size={14}
                    />
                    Origin
                  </span>
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/20">
              {ROWS.map((row) => (
                <tr
                  key={row.key}
                  className="transition-colors duration-150 hover:bg-surface-elevated/60"
                >
                  <td
                    className={`${TD} text-left text-[0.72rem] font-medium text-ink-muted sm:text-xs`}
                  >
                    {row.label}
                  </td>
                  <td className={`${TDM} text-right`}>
                    {renderCell(row.key, targetData)}
                  </td>
                  <td className={`${TDM} text-right`}>
                    {renderCell(row.key, originData)}
                  </td>
                </tr>
              ))}

              {/* Aggregate rows */}
              {totalBeforeUsd != null && (
                <>
                  <tr>
                    <td
                      colSpan={3}
                      className="px-2 pt-3 pb-1 sm:px-3 text-[0.5rem] sm:text-[0.6rem] font-bold uppercase tracking-wider text-ink-muted"
                    >
                      합산 (KRW 환산)
                    </td>
                  </tr>
                  {renderAggRow("합산 손익 전 (USD)", totalBeforeUsd)}
                  {renderAggRow("합산 손익 후 (USD)", totalAfterUsd)}
                  {renderAggRow("합산 손익 전 (USDT)", totalBeforeUsdt)}
                  {renderAggRow("합산 손익 후 (USDT)", totalAfterUsdt)}
                </>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
