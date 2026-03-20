"use client";

import { useCallback, useEffect, useState } from "react";
import { Bell, Plus, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { useAuth } from "../auth/AuthProvider";

const TH =
  "sticky top-0 z-[1] px-2 py-2 sm:px-3 text-[0.5rem] sm:text-[0.65rem] font-bold uppercase tracking-wider text-ink-muted bg-[rgba(10,16,28,0.95)] backdrop-blur-sm whitespace-nowrap";
const TD = "px-2 py-1.5 sm:px-3 sm:py-2 whitespace-nowrap";

function SkeletonRows() {
  const WIDTHS = ["50%", "65%", "40%", "55%", "45%"];
  return Array.from({ length: 3 }).map((_, i) => (
    <tr key={i} className="border-b border-border/10">
      {Array.from({ length: 5 }).map((_, j) => (
        <td key={j} className={TD}>
          <div
            className="h-3 rounded-sm"
            style={{
              width: WIDTHS[(i * 5 + j) % WIDTHS.length],
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

export default function BotVolatilityNotificationsClient({ marketCodeSelectorRef }) {
  const { authorizedRequest } = useAuth();
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [marketCodeOptions, setMarketCodeOptions] = useState([]);
  const [submitting, setSubmitting] = useState(false);
  const [formData, setFormData] = useState({
    marketCombination: "",
    volatilityThreshold: 5,
    notificationIntervalMinutes: 180,
    baseAssets: "",
  });

  const fetchNotifications = useCallback(async () => {
    try {
      const data = await authorizedRequest("/infocore/volatility-notifications/");
      return Array.isArray(data) ? data : data?.results || [];
    } catch {
      return [];
    }
  }, [authorizedRequest]);

  useEffect(() => {
    let active = true;

    async function load() {
      setLoading(true);
      const data = await fetchNotifications();
      if (active) {
        setNotifications(data);
        setLoading(false);
      }
    }

    load();
    return () => {
      active = false;
    };
  }, [fetchNotifications]);

  useEffect(() => {
    let active = true;

    async function loadMarketCodes() {
      try {
        const data = await authorizedRequest("/infocore/market-codes/");
        if (!active || !data) return;

        const options = [];
        for (const [targetMarket, originMarkets] of Object.entries(data)) {
          for (const originMarket of originMarkets) {
            options.push({
              value: `${targetMarket}:${originMarket}`,
              label: `${targetMarket} → ${originMarket}`,
            });
          }
        }
        setMarketCodeOptions(options);

        if (options.length > 0) {
          setFormData((prev) =>
            prev.marketCombination ? prev : { ...prev, marketCombination: options[0].value },
          );
        }
      } catch {
        // ignore
      }
    }

    loadMarketCodes();
    return () => {
      active = false;
    };
  }, [authorizedRequest]);

  async function handleToggleEnabled(notification) {
    try {
      await authorizedRequest(`/infocore/volatility-notifications/${notification.id}/`, {
        method: "PATCH",
        body: { enabled: !notification.enabled },
      });
      setNotifications((prev) =>
        prev.map((n) => (n.id === notification.id ? { ...n, enabled: !n.enabled } : n)),
      );
      toast.success(notification.enabled ? "알림 비활성화" : "알림 활성화");
    } catch {
      toast.error("상태 변경 실패");
    }
  }

  async function handleDelete(id) {
    try {
      await authorizedRequest(`/infocore/volatility-notifications/${id}/`, {
        method: "DELETE",
      });
      toast.success("알림 삭제 완료");
      const data = await fetchNotifications();
      setNotifications(data);
    } catch {
      toast.error("삭제 실패");
    }
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!formData.marketCombination) return;

    const [targetMarketCode, originMarketCode] = formData.marketCombination.split(":");
    const baseAssetsArray = formData.baseAssets
      ? formData.baseAssets
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean)
      : [];

    const body = {
      target_market_code: targetMarketCode,
      origin_market_code: originMarketCode,
      volatility_threshold: (formData.volatilityThreshold / 100).toFixed(6),
      notification_interval_minutes: formData.notificationIntervalMinutes,
      base_assets: baseAssetsArray,
      enabled: true,
    };

    setSubmitting(true);
    try {
      await authorizedRequest("/infocore/volatility-notifications/", {
        method: "POST",
        body,
      });
      toast.success("알림 설정 등록 완료");
      setShowForm(false);
      setFormData({
        marketCombination: marketCodeOptions[0]?.value || "",
        volatilityThreshold: 5,
        notificationIntervalMinutes: 180,
        baseAssets: "",
      });
      const data = await fetchNotifications();
      setNotifications(data);
    } catch {
      toast.error("등록 실패");
    } finally {
      setSubmitting(false);
    }
  }

  void marketCodeSelectorRef;

  return (
    <div className="space-y-4 p-4">
      <div className="flex items-center justify-between">
        <h3 className="section-title">
          <Bell size={15} strokeWidth={2} className="text-accent" />
          변동성 알림
        </h3>
        <button
          className="inline-flex items-center gap-1 rounded-md bg-accent/10 px-2.5 py-1 text-xs font-semibold text-accent transition-colors hover:bg-accent/20"
          onClick={() => setShowForm((v) => !v)}
          type="button"
        >
          <Plus size={13} strokeWidth={2.5} />
          알림 설정 추가
        </button>
      </div>

      {/* Add form */}
      {showForm && (
        <form
          className="space-y-3 rounded-lg border border-accent/20 bg-accent/5 p-3"
          onSubmit={handleSubmit}
        >
          <div>
            <label className="mb-1 block text-xs font-medium text-ink-muted">마켓 조합</label>
            <select
              className="w-full rounded-md border border-border bg-background px-3 py-1.5 text-sm text-ink focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent/30"
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, marketCombination: e.target.value }))
              }
              value={formData.marketCombination}
            >
              {marketCodeOptions.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="mb-1 block text-xs font-medium text-ink-muted">
              변동성 임계값 (%)
            </label>
            <input
              className="w-full rounded-md border border-border bg-background px-3 py-1.5 text-sm text-ink placeholder:text-ink-muted/50 focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent/30"
              min={0}
              onChange={(e) =>
                setFormData((prev) => ({
                  ...prev,
                  volatilityThreshold: parseFloat(e.target.value) || 0,
                }))
              }
              placeholder="5.0"
              step={0.1}
              type="number"
              value={formData.volatilityThreshold}
            />
          </div>

          <div>
            <label className="mb-1 block text-xs font-medium text-ink-muted">알림 간격 (분)</label>
            <input
              className="w-full rounded-md border border-border bg-background px-3 py-1.5 text-sm text-ink placeholder:text-ink-muted/50 focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent/30"
              min={1}
              onChange={(e) =>
                setFormData((prev) => ({
                  ...prev,
                  notificationIntervalMinutes: parseInt(e.target.value, 10) || 1,
                }))
              }
              placeholder="180"
              type="number"
              value={formData.notificationIntervalMinutes}
            />
          </div>

          <div>
            <label className="mb-1 block text-xs font-medium text-ink-muted">
              대상 자산 (쉼표 구분, 비워두면 전체)
            </label>
            <input
              className="w-full rounded-md border border-border bg-background px-3 py-1.5 text-sm text-ink placeholder:text-ink-muted/50 focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent/30"
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, baseAssets: e.target.value }))
              }
              placeholder="BTC, ETH"
              type="text"
              value={formData.baseAssets}
            />
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
              disabled={submitting || !formData.marketCombination}
              type="submit"
            >
              {submitting ? "등록 중..." : "등록"}
            </button>
          </div>
        </form>
      )}

      {/* Notifications table */}
      <div className="rounded-lg border border-border/60 bg-background/80 backdrop-blur-sm overflow-hidden">
        {loading ? (
          <div className="overflow-x-auto">
            <table className="w-full table-auto">
              <thead>
                <tr className="border-b border-border/40">
                  <th className={`${TH} text-left`}>마켓 조합</th>
                  <th className={`${TH} text-right`}>임계값</th>
                  <th className={`${TH} text-right`}>알림 간격</th>
                  <th className={`${TH} text-center`}>상태</th>
                  <th className={`${TH} text-center`}>삭제</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/20">
                <SkeletonRows />
              </tbody>
            </table>
          </div>
        ) : notifications.length === 0 ? (
          <div className="flex flex-col items-center justify-center gap-3 py-16 text-ink-muted">
            <Bell size={32} strokeWidth={1.5} className="text-ink-muted/30" />
            <p className="text-sm">등록된 변동성 알림이 없습니다.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full table-auto">
              <thead>
                <tr className="border-b border-border/40">
                  <th className={`${TH} text-left`}>마켓 조합</th>
                  <th className={`${TH} text-right`}>임계값</th>
                  <th className={`${TH} text-right`}>알림 간격</th>
                  <th className={`${TH} text-center`}>상태</th>
                  <th className={`${TH} text-center`}>삭제</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/20">
                {notifications.map((n) => {
                  const thresholdPct = (Number(n.volatility_threshold) * 100).toFixed(1);
                  const targetShort = n.target_market_code?.split("_")[0] || n.target_market_code;
                  const originShort = n.origin_market_code?.split("_")[0] || n.origin_market_code;

                  return (
                    <tr
                      key={n.id}
                      className="transition-colors duration-150 hover:bg-surface-elevated/60"
                    >
                      <td className={TD}>
                        <span className="text-[0.72rem] font-semibold text-ink sm:text-xs">
                          {targetShort} → {originShort}
                        </span>
                        {n.base_assets?.length > 0 && (
                          <span className="ml-1.5 text-[0.62rem] text-ink-muted">
                            ({n.base_assets.join(", ")})
                          </span>
                        )}
                      </td>
                      <td
                        className={`${TD} text-right text-[0.72rem] tabular-nums text-ink sm:text-xs`}
                      >
                        {thresholdPct}%
                      </td>
                      <td
                        className={`${TD} text-right text-[0.72rem] tabular-nums text-ink sm:text-xs`}
                      >
                        {n.notification_interval_minutes}분
                      </td>
                      <td className={`${TD} text-center`}>
                        <button
                          className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
                            n.enabled ? "bg-accent" : "bg-border"
                          }`}
                          onClick={() => handleToggleEnabled(n)}
                          type="button"
                        >
                          <span
                            className={`inline-block h-3.5 w-3.5 rounded-full bg-white transition-transform ${
                              n.enabled ? "translate-x-4" : "translate-x-0.5"
                            }`}
                          />
                        </button>
                      </td>
                      <td className={`${TD} text-center`}>
                        <button
                          className="inline-flex items-center justify-center rounded-md p-1.5 text-ink-muted/60 transition-colors hover:bg-negative/10 hover:text-negative"
                          onClick={() => handleDelete(n.id)}
                          title="알림 삭제"
                          type="button"
                        >
                          <Trash2 size={14} strokeWidth={2} />
                        </button>
                      </td>
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
