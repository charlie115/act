"use client";

import { useEffect, useState } from "react";
import { Crosshair, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { useAuth } from "../auth/AuthProvider";

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

const STATUS_MAP = {
  0: { label: "대기 (진입)", className: "bg-accent/20 text-accent" },
  "-1": { label: "대기 (탈출)", className: "bg-amber-400/20 text-amber-400" },
  1: { label: "탈출 완료", className: "bg-positive/20 text-positive" },
  "-2": { label: "진입 오류", className: "bg-negative/20 text-negative" },
  2: { label: "탈출 오류", className: "bg-negative/20 text-negative" },
  3: { label: "거래 중", className: "bg-purple-400/20 text-purple-400" },
};

function StatusBadge({ status }) {
  const info = STATUS_MAP[status] ?? { label: `상태 ${status}`, className: "bg-ink-muted/20 text-ink-muted" };
  return (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-[0.65rem] font-bold leading-none ${info.className}`}>
      {info.label}
    </span>
  );
}

function fmtPct(v) {
  if (v == null || v === "") return "-";
  return `${Number(v).toFixed(3)}%`;
}

function fmtNumber(v) {
  if (v == null || v === "") return "-";
  return new Intl.NumberFormat("en-US").format(Number(v));
}

function fmtDate(v) {
  if (!v) return "-";
  const d = new Date(v);
  if (Number.isNaN(d.getTime())) return "-";
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

const TH = "sticky top-0 z-[1] px-2 py-2 sm:px-3 text-[0.5rem] sm:text-[0.65rem] font-bold uppercase tracking-wider text-ink-muted bg-[rgba(10,16,28,0.95)] backdrop-blur-sm whitespace-nowrap";
const TD = "px-2 py-1.5 sm:px-3 sm:py-2 whitespace-nowrap";
const TDM = `${TD} tabular-nums`;

function SkeletonRows() {
  const WIDTHS = ["45%", "70%", "55%", "80%", "60%", "40%", "65%"];
  return Array.from({ length: 5 }).map((_, i) => (
    <tr key={i} className="border-b border-border/10">
      {Array.from({ length: 7 }).map((_, j) => (
        <td key={j} className={TD}>
          <div
            className="h-3 rounded-sm"
            style={{
              width: WIDTHS[(i * 7 + j) % WIDTHS.length],
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

export default function BotTriggersClient({ selectedConfig }) {
  const { authorizedRequest } = useAuth();
  const [trades, setTrades] = useState([]);
  const [loading, setLoading] = useState(!!selectedConfig?.trade_config_uuid);
  const [refreshKey, setRefreshKey] = useState(0);

  const configUuid = selectedConfig?.trade_config_uuid;

  useEffect(() => {
    if (!configUuid) return;
    let active = true;

    async function poll() {
      try {
        const data = await authorizedRequest(
          `/tradecore/trades/?trade_config_uuid=${configUuid}`,
        );
        if (active) {
          setTrades(Array.isArray(data) ? data : data?.results || []);
          setLoading(false);
        }
      } catch {
        if (active) setLoading(false);
      }
    }

    poll();
    const id = setInterval(poll, 3000);
    return () => { active = false; clearInterval(id); };
  }, [configUuid, authorizedRequest, refreshKey]);

  async function handleDelete(uuid) {
    try {
      await authorizedRequest(
        `/tradecore/trades/${uuid}/?trade_config_uuid=${configUuid}`,
        { method: "DELETE" },
      );
      toast.success("트리거 삭제 완료");
      setRefreshKey((k) => k + 1);
    } catch {
      toast.error("삭제 실패");
    }
  }

  return (
    <div className="space-y-4 p-4">
      <h3 className="section-title">
        <Crosshair size={15} strokeWidth={2} className="text-accent" />
        트리거 목록
      </h3>

      <div className="rounded-lg border border-border/60 bg-background/80 backdrop-blur-sm overflow-hidden">
        {loading ? (
          <div className="overflow-x-auto">
            <table className="w-full table-auto">
              <thead>
                <tr className="border-b border-border/40">
                  <th className={`${TH} text-left`}>자산</th>
                  <th className={`${TH} text-right`}>진입 (low)</th>
                  <th className={`${TH} text-right`}>탈출 (high)</th>
                  <th className={`${TH} text-right`}>투자금</th>
                  <th className={`${TH} text-center`}>상태</th>
                  <th className={`${TH} text-right`}>생성일</th>
                  <th className={`${TH} text-center`}>삭제</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/20">
                <SkeletonRows />
              </tbody>
            </table>
          </div>
        ) : trades.length === 0 ? (
          <div className="flex flex-col items-center justify-center gap-3 py-16 text-ink-muted">
            <Crosshair size={32} strokeWidth={1.5} className="text-ink-muted/30" />
            <p className="text-sm">등록된 트리거가 없습니다.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full table-auto">
              <thead>
                <tr className="border-b border-border/40">
                  <th className={`${TH} text-left`}>자산</th>
                  <th className={`${TH} text-right`}>진입 (low)</th>
                  <th className={`${TH} text-right`}>탈출 (high)</th>
                  <th className={`${TH} text-right`}>투자금</th>
                  <th className={`${TH} text-center`}>상태</th>
                  <th className={`${TH} text-right`}>생성일</th>
                  <th className={`${TH} text-center`}>삭제</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/20">
                {trades.map((trade) => (
                  <tr
                    key={trade.uuid || trade.id}
                    className="transition-colors duration-150 hover:bg-surface-elevated/60"
                  >
                    <td className={TD}>
                      <div className="flex items-center gap-1.5">
                        <AssetBadge symbol={trade.base_asset || "?"} size={14} />
                        <span className="text-[0.72rem] sm:text-sm font-semibold text-ink">
                          {trade.base_asset || "-"}
                        </span>
                      </div>
                    </td>
                    <td className={`${TDM} text-right text-[0.72rem] sm:text-xs text-ink`}>
                      {fmtPct(trade.low)}
                    </td>
                    <td className={`${TDM} text-right text-[0.72rem] sm:text-xs text-ink`}>
                      {fmtPct(trade.high)}
                    </td>
                    <td className={`${TDM} text-right text-[0.72rem] sm:text-xs text-ink`}>
                      {fmtNumber(trade.trade_capital)}
                    </td>
                    <td className={`${TD} text-center`}>
                      <StatusBadge status={trade.status} />
                    </td>
                    <td className={`${TDM} text-right text-[0.62rem] sm:text-xs text-ink-muted`}>
                      {fmtDate(trade.created_at || trade.created)}
                    </td>
                    <td className={`${TD} text-center`}>
                      <button
                        className="inline-flex items-center justify-center rounded-md p-1.5 text-ink-muted/60 transition-colors hover:bg-negative/10 hover:text-negative"
                        onClick={() => handleDelete(trade.uuid || trade.id)}
                        title="트리거 삭제"
                        type="button"
                      >
                        <Trash2 size={14} strokeWidth={2} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
