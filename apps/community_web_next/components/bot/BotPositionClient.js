"use client";

import { useEffect, useState } from "react";
import { Activity } from "lucide-react";
import { useAuth } from "../auth/AuthProvider";
import ExchangeIcon from "../ui/ExchangeIcon";

const MINIO_BASE = process.env.NEXT_PUBLIC_MINIO_URL || "http://localhost:19000";
const ASSET_ICON_PATH = `${MINIO_BASE}/community-media/assets/icons`;

function AssetIcon({ symbol, size = 14 }) {
  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      alt={symbol}
      className="rounded-full"
      height={size}
      width={size}
      src={`${ASSET_ICON_PATH}/${symbol}.PNG`}
      onError={(e) => {
        e.currentTarget.style.display = "none";
        if (e.currentTarget.nextSibling) e.currentTarget.nextSibling.style.display = "flex";
      }}
      style={{ objectFit: "cover" }}
    />
  );
}

function AssetBadge({ symbol, size = 14 }) {
  const bg = `hsl(${[...symbol].reduce((a, c) => a + c.charCodeAt(0), 0) % 360}, 55%, 42%)`;
  return (
    <span className="inline-flex flex-shrink-0">
      <AssetIcon symbol={symbol} size={size} />
      <span
        className="items-center justify-center rounded-full font-bold text-white"
        style={{ width: size, height: size, fontSize: size * 0.42, backgroundColor: bg, display: "none" }}
      >
        {symbol.slice(0, 1)}
      </span>
    </span>
  );
}

function HedgeBadge({ isHedged }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-[0.65rem] font-bold leading-none ${
        isHedged ? "bg-positive/20 text-positive" : "bg-negative/20 text-negative"
      }`}
    >
      {isHedged ? "TRUE" : "FALSE"}
    </span>
  );
}

const numFmt = new Intl.NumberFormat("en-US", { maximumFractionDigits: 8 });

function fmtNum(v) {
  if (v == null || v === "") return "-";
  return numFmt.format(Number(v));
}

function numColor(v) {
  if (v == null || v === "") return "text-ink";
  const n = Number(v);
  if (n > 0) return "text-positive";
  if (n < 0) return "text-negative";
  return "text-ink";
}

function fmtPct(v) {
  if (v == null || v === "") return "-";
  return `${Number(v).toFixed(2)}%`;
}

const TH = "sticky top-0 z-[1] px-2 py-2 sm:px-3 text-[0.5rem] sm:text-[0.65rem] font-bold uppercase tracking-wider text-ink-muted bg-[rgba(10,16,28,0.95)] backdrop-blur-sm whitespace-nowrap";
const TD = "px-2 py-1.5 sm:px-3 sm:py-2 whitespace-nowrap";
const TDM = `${TD} tabular-nums`;

function getColumnCount(hasFuturesTarget, hasFuturesOrigin) {
  let cols = 4; // asset, hedge, target pos, origin pos
  if (hasFuturesTarget) cols += 4; // ROI, entry, liq, margin
  if (hasFuturesOrigin) cols += 4;
  return cols;
}

function SkeletonRows({ colCount }) {
  const WIDTHS = ["45%", "70%", "55%", "80%", "60%", "40%", "65%"];
  return Array.from({ length: 5 }).map((_, i) => (
    <tr key={i} className="border-b border-border/10">
      {Array.from({ length: colCount }).map((_, j) => (
        <td key={j} className={TD}>
          <div
            className="h-3 rounded-sm"
            style={{
              width: WIDTHS[(i * colCount + j) % WIDTHS.length],
              background: "linear-gradient(90deg, rgba(255,255,255,0.03), rgba(255,255,255,0.08), rgba(255,255,255,0.03))",
              backgroundSize: "200% 100%",
              animation: "shimmer 1.6s linear infinite",
              animationDelay: `${i * 60}ms`,
            }}
          />
        </td>
      ))}
    </tr>
  ));
}

function mergePositions(targetData, originData, targetIsSpot, originIsSpot) {
  const assetMap = new Map();

  for (const item of targetData) {
    const asset = targetIsSpot ? item.asset : item.base_asset;
    if (!asset) continue;
    const existing = assetMap.get(asset) || { asset, target: null, origin: null };
    existing.target = item;
    assetMap.set(asset, existing);
  }

  for (const item of originData) {
    const asset = originIsSpot ? item.asset : item.base_asset;
    if (!asset) continue;
    const existing = assetMap.get(asset) || { asset, target: null, origin: null };
    existing.origin = item;
    assetMap.set(asset, existing);
  }

  return Array.from(assetMap.values());
}

function getQty(item, isSpot) {
  if (!item) return 0;
  if (isSpot) return Number(item.free || 0);
  return Number(item.qty || 0);
}

export default function BotPositionClient({ marketCodeCombination }) {
  const { authorizedRequest } = useAuth();
  const [positions, setPositions] = useState([]);

  const target = marketCodeCombination?.target;
  const origin = marketCodeCombination?.origin;
  const tradeConfigUuid =
    marketCodeCombination?.tradeConfigUuid || marketCodeCombination?.trade_config_uuid;

  const canFetch = !!(tradeConfigUuid && target && origin);
  const [loading, setLoading] = useState(canFetch);

  const targetIsSpot = target?.isSpot ?? false;
  const originIsSpot = origin?.isSpot ?? false;
  const hasFuturesTarget = !targetIsSpot;
  const hasFuturesOrigin = !originIsSpot;

  useEffect(() => {
    if (!canFetch) return;

    let active = true;

    async function fetchPositions() {
      try {
        const targetEndpoint = targetIsSpot
          ? `/tradecore/spot-position/?market_code=${target.value}&trade_config_uuid=${tradeConfigUuid}`
          : `/tradecore/futures-position/?market_code=${target.value}&trade_config_uuid=${tradeConfigUuid}`;
        const originEndpoint = originIsSpot
          ? `/tradecore/spot-position/?market_code=${origin.value}&trade_config_uuid=${tradeConfigUuid}`
          : `/tradecore/futures-position/?market_code=${origin.value}&trade_config_uuid=${tradeConfigUuid}`;

        const [targetRes, originRes] = await Promise.all([
          authorizedRequest(targetEndpoint),
          authorizedRequest(originEndpoint),
        ]);

        if (active) {
          const targetData = Array.isArray(targetRes) ? targetRes : targetRes?.results || [];
          const originData = Array.isArray(originRes) ? originRes : originRes?.results || [];
          setPositions(mergePositions(targetData, originData, targetIsSpot, originIsSpot));
          setLoading(false);
        }
      } catch {
        if (active) {
          setPositions([]);
          setLoading(false);
        }
      }
    }

    fetchPositions();

    return () => {
      active = false;
    };
  }, [canFetch, tradeConfigUuid, target, origin, targetIsSpot, originIsSpot, authorizedRequest]);

  const colCount = getColumnCount(hasFuturesTarget, hasFuturesOrigin);

  return (
    <div className="space-y-4 p-4">
      <h3 className="section-title">
        <Activity size={15} strokeWidth={2} className="text-accent" />
        포지션 현황
      </h3>

      {/* Sub-header: exchange labels */}
      {target && origin && (
        <div className="flex items-center gap-4 text-[0.72rem] text-ink-muted">
          <span className="inline-flex items-center gap-1.5">
            <ExchangeIcon exchange={target.exchange} size={16} />
            <span>{target.label || target.getLabel?.()}</span>
            <span className="text-accent/60">Target</span>
          </span>
          <span className="text-border">|</span>
          <span className="inline-flex items-center gap-1.5">
            <ExchangeIcon exchange={origin.exchange} size={16} />
            <span>{origin.label || origin.getLabel?.()}</span>
            <span className="text-accent/60">Origin</span>
          </span>
        </div>
      )}

      <div className="rounded-lg border border-border/60 bg-background/80 backdrop-blur-sm overflow-hidden">
        {loading ? (
          <div className="overflow-x-auto">
            <table className="w-full table-auto">
              <thead>
                <tr className="border-b border-border/40">
                  <th className={`${TH} text-left`}>Asset</th>
                  <th className={`${TH} text-center`}>Hedge</th>
                  <th className={`${TH} text-right`}>Target Pos</th>
                  <th className={`${TH} text-right`}>Origin Pos</th>
                  {hasFuturesTarget && (
                    <>
                      <th className={`${TH} text-right`}>T. ROI</th>
                      <th className={`${TH} text-right`}>T. Entry</th>
                      <th className={`${TH} text-right`}>T. Liq.</th>
                      <th className={`${TH} text-center`}>T. Margin</th>
                    </>
                  )}
                  {hasFuturesOrigin && (
                    <>
                      <th className={`${TH} text-right`}>O. ROI</th>
                      <th className={`${TH} text-right`}>O. Entry</th>
                      <th className={`${TH} text-right`}>O. Liq.</th>
                      <th className={`${TH} text-center`}>O. Margin</th>
                    </>
                  )}
                </tr>
              </thead>
              <tbody className="divide-y divide-border/20">
                <SkeletonRows colCount={colCount} />
              </tbody>
            </table>
          </div>
        ) : positions.length === 0 ? (
          <div className="flex flex-col items-center justify-center gap-3 py-16 text-ink-muted">
            <Activity size={32} strokeWidth={1.5} className="text-ink-muted/30" />
            <p className="text-sm">활성 포지션이 없습니다.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full table-auto">
              <thead>
                <tr className="border-b border-border/40">
                  <th className={`${TH} text-left`}>Asset</th>
                  <th className={`${TH} text-center`}>Hedge</th>
                  <th className={`${TH} text-right`}>Target Pos</th>
                  <th className={`${TH} text-right`}>Origin Pos</th>
                  {hasFuturesTarget && (
                    <>
                      <th className={`${TH} text-right`}>T. ROI</th>
                      <th className={`${TH} text-right`}>T. Entry</th>
                      <th className={`${TH} text-right`}>T. Liq.</th>
                      <th className={`${TH} text-center`}>T. Margin</th>
                    </>
                  )}
                  {hasFuturesOrigin && (
                    <>
                      <th className={`${TH} text-right`}>O. ROI</th>
                      <th className={`${TH} text-right`}>O. Entry</th>
                      <th className={`${TH} text-right`}>O. Liq.</th>
                      <th className={`${TH} text-center`}>O. Margin</th>
                    </>
                  )}
                </tr>
              </thead>
              <tbody className="divide-y divide-border/20">
                {positions.map((row) => {
                  const targetQty = getQty(row.target, targetIsSpot);
                  const originQty = getQty(row.origin, originIsSpot);
                  const isHedged = Math.abs(targetQty + originQty) <= 0.5;

                  return (
                    <tr
                      key={row.asset}
                      className="transition-colors duration-150 hover:bg-surface-elevated/60"
                    >
                      {/* Asset */}
                      <td className={TD}>
                        <div className="flex items-center gap-1.5">
                          <AssetBadge symbol={row.asset} size={14} />
                          <span className="text-[0.72rem] sm:text-sm font-semibold text-ink">
                            {row.asset}
                          </span>
                        </div>
                      </td>

                      {/* Hedge */}
                      <td className={`${TD} text-center`}>
                        <HedgeBadge isHedged={isHedged} />
                      </td>

                      {/* Target Pos */}
                      <td className={`${TDM} text-right text-[0.72rem] sm:text-xs ${numColor(targetQty)}`}>
                        {fmtNum(targetQty)}
                      </td>

                      {/* Origin Pos */}
                      <td className={`${TDM} text-right text-[0.72rem] sm:text-xs ${numColor(originQty)}`}>
                        {fmtNum(originQty)}
                      </td>

                      {/* Futures target columns */}
                      {hasFuturesTarget && (
                        <>
                          <td className={`${TDM} text-right text-[0.72rem] sm:text-xs ${numColor(row.target?.ROI)}`}>
                            {fmtPct(row.target?.ROI)}
                          </td>
                          <td className={`${TDM} text-right text-[0.72rem] sm:text-xs text-ink`}>
                            {fmtNum(row.target?.entry_price)}
                          </td>
                          <td className={`${TDM} text-right text-[0.72rem] sm:text-xs text-ink-muted`}>
                            {fmtNum(row.target?.liquidation_price)}
                          </td>
                          <td className={`${TD} text-center text-[0.65rem] sm:text-xs text-ink-muted`}>
                            {row.target?.margin_type || "-"}
                          </td>
                        </>
                      )}

                      {/* Futures origin columns */}
                      {hasFuturesOrigin && (
                        <>
                          <td className={`${TDM} text-right text-[0.72rem] sm:text-xs ${numColor(row.origin?.ROI)}`}>
                            {fmtPct(row.origin?.ROI)}
                          </td>
                          <td className={`${TDM} text-right text-[0.72rem] sm:text-xs text-ink`}>
                            {fmtNum(row.origin?.entry_price)}
                          </td>
                          <td className={`${TDM} text-right text-[0.72rem] sm:text-xs text-ink-muted`}>
                            {fmtNum(row.origin?.liquidation_price)}
                          </td>
                          <td className={`${TD} text-center text-[0.65rem] sm:text-xs text-ink-muted`}>
                            {row.origin?.margin_type || "-"}
                          </td>
                        </>
                      )}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
