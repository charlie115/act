"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { ChevronLeft, ChevronRight, History } from "lucide-react";
import { useAuth } from "../auth/AuthProvider";

/* ------------------------------------------------------------------ */
/*  Formatting helpers                                                 */
/* ------------------------------------------------------------------ */

const numFmt = new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 });

function fmtPnl(v) {
  if (v == null || v === "") return "-";
  const n = Number(v);
  const prefix = n > 0 ? "+" : "";
  return `${prefix}${numFmt.format(n)}`;
}

function fmtPct(v) {
  if (v == null || v === "") return "-";
  const n = Number(v);
  const prefix = n > 0 ? "+" : "";
  return `${prefix}${n.toFixed(3)}%`;
}

function pnlColor(v) {
  if (v == null || v === "") return "text-ink";
  const n = Number(v);
  if (n > 0) return "text-positive";
  if (n < 0) return "text-negative";
  return "text-ink";
}

function fmtDate(v) {
  if (!v) return "-";
  const d = new Date(v);
  if (Number.isNaN(d.getTime())) return "-";
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

/* ------------------------------------------------------------------ */
/*  Table class constants (matches BotTriggersClient)                  */
/* ------------------------------------------------------------------ */

const TH =
  "sticky top-0 z-[1] px-2 py-2 sm:px-3 text-[0.5rem] sm:text-[0.65rem] font-bold uppercase tracking-wider text-ink-muted bg-[rgba(10,16,28,0.95)] backdrop-blur-sm whitespace-nowrap";
const TD = "px-2 py-1.5 sm:px-3 sm:py-2 whitespace-nowrap";
const TDM = `${TD} tabular-nums`;

const PAGE_SIZE = 20;

/* ------------------------------------------------------------------ */
/*  Shimmer skeleton                                                   */
/* ------------------------------------------------------------------ */

const COL_COUNT = 6;
const WIDTHS = ["45%", "55%", "65%", "70%", "60%", "50%"];

function SkeletonRows() {
  return Array.from({ length: 6 }).map((_, i) => (
    <tr key={i} className="border-b border-border/10">
      {Array.from({ length: COL_COUNT }).map((_, j) => (
        <td key={j} className={TD}>
          <div
            className="h-3 rounded-sm"
            style={{
              width: WIDTHS[(i * COL_COUNT + j) % WIDTHS.length],
              background:
                "linear-gradient(90deg, rgba(255,255,255,0.03), rgba(255,255,255,0.08), rgba(255,255,255,0.03))",
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

/* ------------------------------------------------------------------ */
/*  Table header row                                                   */
/* ------------------------------------------------------------------ */

function TableHead() {
  return (
    <thead>
      <tr className="border-b border-border/40">
        <th className={`${TH} text-left`}>거래일</th>
        <th className={`${TH} text-right`}>실현 김프</th>
        <th className={`${TH} text-right`}>Target 손익</th>
        <th className={`${TH} text-right`}>Origin 손익</th>
        <th className={`${TH} text-right`}>합산 손익</th>
        <th className={`${TH} text-right`}>합산 (김프보정)</th>
      </tr>
    </thead>
  );
}

/* ------------------------------------------------------------------ */
/*  Main component                                                     */
/* ------------------------------------------------------------------ */

export default function BotPnlHistoryClient({ marketCodeCombination }) {
  const { authorizedRequest } = useAuth();
  const [history, setHistory] = useState([]);
  const [page, setPage] = useState(0);

  const configUuid =
    marketCodeCombination?.tradeConfigUuid ||
    marketCodeCombination?.trade_config_uuid;

  const [loading, setLoading] = useState(!!configUuid);

  /* ---------- Fetch data ------------------------------------------ */

  const fetchHistory = useCallback(async () => {
    if (!configUuid) return;
    try {
      const data = await authorizedRequest(
        `/tradecore/pnl-history/?trade_config_uuid=${configUuid}`,
      );
      return Array.isArray(data) ? data : data?.results || [];
    } catch {
      return [];
    }
  }, [configUuid, authorizedRequest]);

  useEffect(() => {
    if (!configUuid) return;

    let active = true;

    fetchHistory().then((rows) => {
      if (active) {
        setHistory(rows || []);
        setLoading(false);
        setPage(0);
      }
    });

    return () => {
      active = false;
    };
  }, [configUuid, fetchHistory]);

  /* ---------- Sort (newest first) --------------------------------- */

  const sorted = useMemo(
    () =>
      [...history].sort(
        (a, b) =>
          new Date(b.registered_datetime).getTime() -
          new Date(a.registered_datetime).getTime(),
      ),
    [history],
  );

  /* ---------- Summary stats --------------------------------------- */

  const stats = useMemo(() => {
    if (!sorted.length)
      return { count: 0, totalPnl: 0, avgPnl: 0, winRate: 0 };

    const totalPnl = sorted.reduce(
      (sum, r) => sum + (Number(r.total_pnl_after_fee) || 0),
      0,
    );
    const wins = sorted.filter(
      (r) => Number(r.total_pnl_after_fee) > 0,
    ).length;

    return {
      count: sorted.length,
      totalPnl,
      avgPnl: totalPnl / sorted.length,
      winRate: (wins / sorted.length) * 100,
    };
  }, [sorted]);

  /* ---------- Pagination ------------------------------------------ */

  const totalPages = Math.max(1, Math.ceil(sorted.length / PAGE_SIZE));
  const pageRows = sorted.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  /* ---------- Render ---------------------------------------------- */

  return (
    <div className="space-y-4 p-4">
      <h3 className="section-title">
        <History size={15} strokeWidth={2} className="text-accent" />
        손익 히스토리
      </h3>

      {/* Summary stat cards */}
      {!loading && sorted.length > 0 && (
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4 sm:gap-3">
          <StatCard label="총 거래" value={`${stats.count}건`} />
          <StatCard
            label="총 손익"
            value={fmtPnl(stats.totalPnl)}
            colorClass={pnlColor(stats.totalPnl)}
          />
          <StatCard
            label="평균 손익"
            value={fmtPnl(stats.avgPnl)}
            colorClass={pnlColor(stats.avgPnl)}
          />
          <StatCard
            label="승률"
            value={`${stats.winRate.toFixed(1)}%`}
            colorClass={
              stats.winRate >= 50 ? "text-positive" : "text-negative"
            }
          />
        </div>
      )}

      {/* Table */}
      <div className="rounded-lg border border-border/60 bg-background/80 backdrop-blur-sm overflow-hidden">
        {loading ? (
          <div className="overflow-x-auto">
            <table className="w-full table-auto">
              <TableHead />
              <tbody className="divide-y divide-border/20">
                <SkeletonRows />
              </tbody>
            </table>
          </div>
        ) : sorted.length === 0 ? (
          <div className="flex flex-col items-center justify-center gap-3 py-16 text-ink-muted">
            <History
              size={32}
              strokeWidth={1.5}
              className="text-ink-muted/30"
            />
            <p className="text-sm">손익 기록이 없습니다.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full table-auto">
              <TableHead />
              <tbody className="divide-y divide-border/20">
                {pageRows.map((row) => (
                  <tr
                    key={row.uuid || row.trade_uuid}
                    className="transition-colors duration-150 hover:bg-surface-elevated/60"
                  >
                    {/* 거래일 */}
                    <td
                      className={`${TDM} text-left text-[0.62rem] sm:text-xs text-ink-muted`}
                    >
                      {fmtDate(row.registered_datetime)}
                    </td>

                    {/* 실현 김프 */}
                    <td
                      className={`${TDM} text-right text-[0.72rem] sm:text-xs ${pnlColor(row.realized_premium_gap_p)}`}
                    >
                      {fmtPct(row.realized_premium_gap_p)}
                    </td>

                    {/* Target 손익 */}
                    <td
                      className={`${TDM} text-right text-[0.72rem] sm:text-xs ${pnlColor(row.target_pnl_after_fee)}`}
                    >
                      {fmtPnl(row.target_pnl_after_fee)}
                      {row.target_currency ? (
                        <span className="ml-0.5 text-[0.5rem] text-ink-muted">
                          {row.target_currency}
                        </span>
                      ) : null}
                    </td>

                    {/* Origin 손익 */}
                    <td
                      className={`${TDM} text-right text-[0.72rem] sm:text-xs ${pnlColor(row.origin_pnl_after_fee)}`}
                    >
                      {fmtPnl(row.origin_pnl_after_fee)}
                      {row.origin_currency ? (
                        <span className="ml-0.5 text-[0.5rem] text-ink-muted">
                          {row.origin_currency}
                        </span>
                      ) : null}
                    </td>

                    {/* 합산 손익 */}
                    <td
                      className={`${TDM} text-right text-[0.72rem] sm:text-xs font-bold ${pnlColor(row.total_pnl_after_fee)}`}
                    >
                      {fmtPnl(row.total_pnl_after_fee)}
                    </td>

                    {/* 합산 (김프보정) */}
                    <td
                      className={`${TDM} text-right text-[0.72rem] sm:text-xs ${pnlColor(row.total_pnl_after_fee_kimp)}`}
                    >
                      {fmtPnl(row.total_pnl_after_fee_kimp)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Pagination */}
      {!loading && sorted.length > PAGE_SIZE && (
        <div className="flex items-center justify-between px-1">
          <span className="text-[0.65rem] tabular-nums text-ink-muted">
            {page * PAGE_SIZE + 1}&ndash;
            {Math.min((page + 1) * PAGE_SIZE, sorted.length)} / {sorted.length}
          </span>
          <div className="flex items-center gap-1">
            <button
              className="inline-flex items-center justify-center rounded-md px-2 py-1 text-[0.65rem] font-semibold text-ink-muted transition-colors hover:bg-surface-elevated/60 disabled:opacity-30 disabled:cursor-not-allowed"
              disabled={page === 0}
              onClick={() => setPage((p) => p - 1)}
              type="button"
            >
              <ChevronLeft size={14} strokeWidth={2} />
              이전
            </button>
            <span className="px-2 text-[0.65rem] tabular-nums text-ink-muted">
              {page + 1} / {totalPages}
            </span>
            <button
              className="inline-flex items-center justify-center rounded-md px-2 py-1 text-[0.65rem] font-semibold text-ink-muted transition-colors hover:bg-surface-elevated/60 disabled:opacity-30 disabled:cursor-not-allowed"
              disabled={page >= totalPages - 1}
              onClick={() => setPage((p) => p + 1)}
              type="button"
            >
              다음
              <ChevronRight size={14} strokeWidth={2} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Stat card sub-component                                            */
/* ------------------------------------------------------------------ */

function StatCard({ label, value, colorClass = "text-ink" }) {
  return (
    <div className="rounded-lg border border-border/40 bg-surface-elevated/30 px-3 py-2.5">
      <p className="text-[0.55rem] sm:text-[0.65rem] font-bold uppercase tracking-wider text-ink-muted">
        {label}
      </p>
      <p className={`mt-0.5 text-sm sm:text-base font-bold tabular-nums ${colorClass}`}>
        {value}
      </p>
    </div>
  );
}
