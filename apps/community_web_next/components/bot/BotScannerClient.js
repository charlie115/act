"use client";

import { useEffect, useState } from "react";
import { ChevronDown, ChevronUp, Plus, ScanLine, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { useAuth } from "../auth/AuthProvider";

const TH =
  "sticky top-0 z-[1] px-2 py-2 sm:px-3 text-[0.5rem] sm:text-[0.65rem] font-bold uppercase tracking-wider text-ink-muted bg-[rgba(10,16,28,0.95)] backdrop-blur-sm whitespace-nowrap";
const TD = "px-2 py-1.5 sm:px-3 sm:py-2 whitespace-nowrap";
const TDM = `${TD} tabular-nums`;

const INPUT_CLS =
  "w-full rounded-md border border-border bg-background px-3 py-1.5 text-sm text-ink placeholder:text-ink-muted/50 focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent/30";

function fmtPct(v) {
  if (v == null || v === "") return "-";
  return `${Number(v).toFixed(3)}%`;
}

function fmtCurrency(v) {
  if (v == null || v === "") return "-";
  return new Intl.NumberFormat("en-US").format(Number(v));
}

function fmtAtp(v) {
  if (v == null || v === "") return "-";
  const num = Number(v) / 100_000_000;
  return `${num.toLocaleString("en-US", { maximumFractionDigits: 1 })}억`;
}

function fmtFundingRate(v) {
  if (v == null || v === "") return "-";
  return `${(Number(v) * 100).toFixed(4)}%`;
}

function SkeletonRows() {
  const WIDTHS = ["45%", "70%", "55%", "80%", "60%", "40%", "65%"];
  return Array.from({ length: 4 }).map((_, i) => (
    <tr key={i} className="border-b border-border/10">
      {Array.from({ length: 7 }).map((_, j) => (
        <td key={j} className={TD}>
          <div
            className="h-3 rounded-sm"
            style={{
              width: WIDTHS[(i * 7 + j) % WIDTHS.length],
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

const INITIAL_FORM = {
  low: "",
  high: "",
  trade_capital: "",
  min_target_atp: "",
  min_target_funding_rate: "",
  max_repeat_num: "5",
  repeat_term_secs: "300",
};

export default function BotScannerClient({ selectedConfig }) {
  const { authorizedRequest } = useAuth();
  const [scanners, setScanners] = useState([]);
  const [loading, setLoading] = useState(!!selectedConfig?.trade_config_uuid);
  const [refreshKey, setRefreshKey] = useState(0);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState(INITIAL_FORM);
  const [submitting, setSubmitting] = useState(false);

  const configUuid = selectedConfig?.trade_config_uuid;

  useEffect(() => {
    if (!configUuid) return;
    let active = true;

    async function poll() {
      try {
        const data = await authorizedRequest(
          `/tradecore/trigger-scanner/?trade_config_uuid=${configUuid}`,
        );
        if (active) {
          setScanners(Array.isArray(data) ? data : data?.results || []);
          setLoading(false);
        }
      } catch {
        if (active) setLoading(false);
      }
    }

    poll();
    const id = setInterval(poll, 3000);
    return () => {
      active = false;
      clearInterval(id);
    };
  }, [configUuid, authorizedRequest, refreshKey]);

  async function handleDelete(uuid) {
    try {
      await authorizedRequest(`/tradecore/trigger-scanner/${uuid}/`, {
        method: "DELETE",
      });
      toast.success("스캐너 삭제 완료");
      setRefreshKey((k) => k + 1);
    } catch {
      toast.error("삭제 실패");
    }
  }

  function handleFormChange(field, value) {
    setFormData((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();

    const low = parseFloat(formData.low);
    const high = parseFloat(formData.high);
    const tradeCapital = parseInt(formData.trade_capital, 10);

    if (Number.isNaN(low) || Number.isNaN(high) || low >= high) {
      toast.error("진입(%) 값은 탈출(%) 값보다 작아야 합니다.");
      return;
    }
    if (Number.isNaN(tradeCapital) || tradeCapital < 10000) {
      toast.error("투자금은 최소 10,000 이상이어야 합니다.");
      return;
    }

    const body = {
      trade_config_uuid: configUuid,
      low: String(low),
      high: String(high),
      trade_capital: tradeCapital,
      max_repeat_num: parseInt(formData.max_repeat_num, 10) || 5,
      repeat_term_secs: parseInt(formData.repeat_term_secs, 10) || 300,
    };

    if (formData.min_target_atp !== "") {
      body.min_target_atp = String(
        parseFloat(formData.min_target_atp) * 100_000_000,
      );
    }
    if (formData.min_target_funding_rate !== "") {
      body.min_target_funding_rate = String(
        parseFloat(formData.min_target_funding_rate) / 100,
      );
    }

    setSubmitting(true);
    try {
      await authorizedRequest("/tradecore/trigger-scanner/", {
        method: "POST",
        body,
      });
      toast.success("스캐너 등록 완료");
      setShowForm(false);
      setFormData(INITIAL_FORM);
      setRefreshKey((k) => k + 1);
    } catch (err) {
      toast.error(err?.detail || "등록 실패");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-4 p-4">
      <h3 className="section-title">
        <ScanLine size={15} strokeWidth={2} className="text-accent" />
        트리거 스캐너
      </h3>

      <div className="rounded-lg border border-border/60 bg-background/80 backdrop-blur-sm overflow-hidden">
        {loading ? (
          <div className="overflow-x-auto">
            <table className="w-full table-auto">
              <thead>
                <tr className="border-b border-border/40">
                  <th className={`${TH} text-right`}>진입</th>
                  <th className={`${TH} text-right`}>탈출</th>
                  <th className={`${TH} text-right`}>투자금</th>
                  <th className={`${TH} text-right`}>최소거래량</th>
                  <th className={`${TH} text-right`}>최소펀딩</th>
                  <th className={`${TH} text-center`}>반복</th>
                  <th className={`${TH} text-center`}>삭제</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/20">
                <SkeletonRows />
              </tbody>
            </table>
          </div>
        ) : scanners.length === 0 ? (
          <div className="flex flex-col items-center justify-center gap-3 py-16 text-ink-muted">
            <ScanLine size={32} strokeWidth={1.5} className="text-ink-muted/30" />
            <p className="text-sm">등록된 스캐너가 없습니다.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full table-auto">
              <thead>
                <tr className="border-b border-border/40">
                  <th className={`${TH} text-right`}>진입</th>
                  <th className={`${TH} text-right`}>탈출</th>
                  <th className={`${TH} text-right`}>투자금</th>
                  <th className={`${TH} text-right`}>최소거래량</th>
                  <th className={`${TH} text-right`}>최소펀딩</th>
                  <th className={`${TH} text-center`}>반복</th>
                  <th className={`${TH} text-center`}>삭제</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/20">
                {scanners.map((scanner) => (
                  <tr
                    key={scanner.uuid}
                    className="transition-colors duration-150 hover:bg-surface-elevated/60"
                  >
                    <td className={`${TDM} text-right text-[0.72rem] sm:text-xs text-ink`}>
                      {fmtPct(scanner.low)}
                    </td>
                    <td className={`${TDM} text-right text-[0.72rem] sm:text-xs text-ink`}>
                      {fmtPct(scanner.high)}
                    </td>
                    <td className={`${TDM} text-right text-[0.72rem] sm:text-xs text-ink`}>
                      {fmtCurrency(scanner.trade_capital)}
                    </td>
                    <td className={`${TDM} text-right text-[0.72rem] sm:text-xs text-ink`}>
                      {fmtAtp(scanner.min_target_atp)}
                    </td>
                    <td className={`${TDM} text-right text-[0.72rem] sm:text-xs text-ink`}>
                      {fmtFundingRate(scanner.min_target_funding_rate)}
                    </td>
                    <td className={`${TDM} text-center text-[0.72rem] sm:text-xs text-ink`}>
                      {scanner.curr_repeat_num} / {scanner.max_repeat_num}
                    </td>
                    <td className={`${TD} text-center`}>
                      <button
                        className="inline-flex items-center justify-center rounded-md p-1.5 text-ink-muted/60 transition-colors hover:bg-negative/10 hover:text-negative"
                        onClick={() => handleDelete(scanner.uuid)}
                        title="스캐너 삭제"
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

      {/* Add scanner toggle */}
      <button
        className="inline-flex items-center gap-1.5 rounded-md bg-accent/10 px-3 py-1.5 text-xs font-semibold text-accent transition-colors hover:bg-accent/20"
        onClick={() => {
          setShowForm((v) => !v);
          if (!showForm) setFormData(INITIAL_FORM);
        }}
        type="button"
      >
        {showForm ? (
          <>
            <ChevronUp size={14} strokeWidth={2} />
            닫기
          </>
        ) : (
          <>
            <Plus size={14} strokeWidth={2} />
            스캐너 추가
          </>
        )}
      </button>

      {/* Add scanner form */}
      {showForm && (
        <form
          className="space-y-3 rounded-lg border border-accent/20 bg-accent/5 p-3"
          onSubmit={handleSubmit}
        >
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
            <div>
              <label className="mb-1 block text-xs font-medium text-ink-muted">
                진입 (%)
              </label>
              <input
                autoFocus
                className={INPUT_CLS}
                onChange={(e) => handleFormChange("low", e.target.value)}
                placeholder="1.500"
                required
                step="any"
                type="number"
                value={formData.low}
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-ink-muted">
                탈출 (%)
              </label>
              <input
                className={INPUT_CLS}
                onChange={(e) => handleFormChange("high", e.target.value)}
                placeholder="3.000"
                required
                step="any"
                type="number"
                value={formData.high}
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-ink-muted">
                투자금
              </label>
              <input
                className={INPUT_CLS}
                min="10000"
                onChange={(e) => handleFormChange("trade_capital", e.target.value)}
                placeholder="50000"
                required
                type="number"
                value={formData.trade_capital}
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-ink-muted">
                최소거래량 (억)
              </label>
              <input
                className={INPUT_CLS}
                onChange={(e) => handleFormChange("min_target_atp", e.target.value)}
                placeholder="5"
                step="any"
                type="number"
                value={formData.min_target_atp}
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-ink-muted">
                최소펀딩률 (%)
              </label>
              <input
                className={INPUT_CLS}
                onChange={(e) =>
                  handleFormChange("min_target_funding_rate", e.target.value)
                }
                placeholder="0.01"
                step="any"
                type="number"
                value={formData.min_target_funding_rate}
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-ink-muted">
                최대반복횟수
              </label>
              <input
                className={INPUT_CLS}
                min="1"
                onChange={(e) => handleFormChange("max_repeat_num", e.target.value)}
                placeholder="5"
                required
                type="number"
                value={formData.max_repeat_num}
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-ink-muted">
                반복간격 (초)
              </label>
              <input
                className={INPUT_CLS}
                min="1"
                onChange={(e) =>
                  handleFormChange("repeat_term_secs", e.target.value)
                }
                placeholder="300"
                required
                type="number"
                value={formData.repeat_term_secs}
              />
            </div>
          </div>

          <div className="flex items-center justify-end gap-2 pt-1">
            <button
              className="rounded-md px-3 py-1.5 text-xs font-semibold text-ink-muted transition-colors hover:bg-surface-elevated"
              onClick={() => setShowForm(false)}
              type="button"
            >
              취소
            </button>
            <button
              className="rounded-md bg-accent px-3 py-1.5 text-xs font-semibold text-white transition-colors hover:bg-accent/90 disabled:opacity-50"
              disabled={submitting || !formData.low || !formData.high || !formData.trade_capital}
              type="submit"
            >
              {submitting ? "등록 중..." : "등록"}
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
