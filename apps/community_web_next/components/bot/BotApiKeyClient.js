"use client";

import { useCallback, useEffect, useState } from "react";
import { Eye, EyeOff, Plus, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { useAuth } from "../auth/AuthProvider";
import ExchangeIcon from "../ui/ExchangeIcon";

export default function BotApiKeyClient({ marketCodeCombination, selectedConfig }) {
  const { authorizedRequest } = useAuth();
  const [keys, setKeys] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(null); // "target" | "origin" | null
  const [formData, setFormData] = useState({ access_key: "", secret_key: "", passphrase: "" });
  const [showSecret, setShowSecret] = useState(false);
  const [showPassphrase, setShowPassphrase] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(null);

  const nodeIp = selectedConfig?.url
    ? selectedConfig.url.split("://")[1]?.split(":")[0]
    : null;

  const fetchKeys = useCallback(async () => {
    if (!selectedConfig?.trade_config_uuid) return;
    try {
      const data = await authorizedRequest(
        `/tradecore/exchange-api-key/?trade_config_uuid=${selectedConfig.trade_config_uuid}`
      );
      setKeys(Array.isArray(data) ? data : data?.results || []);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, [selectedConfig?.trade_config_uuid, authorizedRequest]);

  useEffect(() => {
    if (!selectedConfig?.trade_config_uuid) return;
    let active = true;
    setLoading(true);
    authorizedRequest(
      `/tradecore/exchange-api-key/?trade_config_uuid=${selectedConfig.trade_config_uuid}`
    )
      .then((data) => {
        if (active) {
          setKeys(Array.isArray(data) ? data : data?.results || []);
          setLoading(false);
        }
      })
      .catch(() => {
        if (active) setLoading(false);
      });
    return () => { active = false; };
  }, [selectedConfig?.trade_config_uuid, authorizedRequest]);

  async function handleCreate(marketCode) {
    const body = {
      trade_config_uuid: selectedConfig.trade_config_uuid,
      market_code: marketCode,
      access_key: formData.access_key,
      secret_key: formData.secret_key,
    };
    if (formData.passphrase) body.passphrase = formData.passphrase;

    setSubmitting(true);
    try {
      await authorizedRequest("/tradecore/exchange-api-key/", { method: "POST", body });
      toast.success("API 키 등록 완료");
      setShowForm(null);
      setFormData({ access_key: "", secret_key: "", passphrase: "" });
      setShowSecret(false);
      setShowPassphrase(false);
      await fetchKeys();
    } catch (err) {
      toast.error(err?.detail || "등록 실패");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(uuid) {
    try {
      await authorizedRequest(
        `/tradecore/exchange-api-key/${uuid}/?trade_config_uuid=${selectedConfig.trade_config_uuid}`,
        { method: "DELETE" }
      );
      toast.success("API 키 삭제 완료");
      setConfirmDelete(null);
      await fetchKeys();
    } catch {
      toast.error("삭제 실패");
    }
  }

  if (loading) {
    return (
      <div className="grid place-items-center py-12">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-border border-t-accent" />
      </div>
    );
  }

  const targetMarket = marketCodeCombination?.target;
  const originMarket = marketCodeCombination?.origin;
  const targetKeys = keys.filter((k) => k.market_code === targetMarket?.value);
  const originKeys = keys.filter((k) => k.market_code === originMarket?.value);

  function renderKeyTable(side, market, marketKeys) {
    const exchange = market?.exchange;
    const isOkx = exchange === "OKX";

    return (
      <div className="rounded-lg border border-border/60 bg-background/80 p-4">
        {/* Header */}
        <div className="mb-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ExchangeIcon exchange={exchange} size={20} />
            <span className="text-sm font-semibold text-ink">
              {market?.getLabel?.() || market?.label || side}
            </span>
          </div>
          <button
            className="inline-flex items-center gap-1 rounded-md bg-accent/10 px-2.5 py-1 text-xs font-semibold text-accent transition-colors hover:bg-accent/20"
            onClick={() => {
              setShowForm(side);
              setFormData({ access_key: "", secret_key: "", passphrase: "" });
              setShowSecret(false);
              setShowPassphrase(false);
            }}
            type="button"
          >
            <Plus size={13} strokeWidth={2.5} />
            API 키 등록
          </button>
        </div>

        {/* Key table */}
        {marketKeys.length === 0 ? (
          <p className="py-6 text-center text-xs text-ink-muted">등록된 API 키가 없습니다.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-border/40 text-ink-muted">
                  <th className="pb-2 pr-3 font-medium">등록일</th>
                  <th className="pb-2 pr-3 font-medium">Access Key</th>
                  <th className="pb-2 pr-3 font-medium">Secret Key</th>
                  <th className="pb-2 font-medium" />
                </tr>
              </thead>
              <tbody>
                {marketKeys.map((k) => (
                  <tr key={k.uuid || k.id} className="border-b border-border/20 last:border-0">
                    <td className="py-2 pr-3 text-ink-muted">
                      {k.registered_datetime
                        ? new Date(k.registered_datetime).toLocaleDateString("ko-KR")
                        : "-"}
                    </td>
                    <td className="py-2 pr-3">
                      <span className="inline-block max-w-[200px] truncate text-ink">
                        {k.access_key}
                      </span>
                    </td>
                    <td className="py-2 pr-3 text-ink-muted">●●●●●●●●</td>
                    <td className="py-2 text-right">
                      {confirmDelete === (k.uuid || k.id) ? (
                        <span className="inline-flex items-center gap-1.5">
                          <button
                            className="rounded px-1.5 py-0.5 text-[0.68rem] font-semibold text-negative hover:bg-negative/10"
                            onClick={() => handleDelete(k.uuid || k.id)}
                            type="button"
                          >
                            확인
                          </button>
                          <button
                            className="rounded px-1.5 py-0.5 text-[0.68rem] font-semibold text-ink-muted hover:bg-surface-elevated"
                            onClick={() => setConfirmDelete(null)}
                            type="button"
                          >
                            취소
                          </button>
                        </span>
                      ) : (
                        <button
                          className="rounded p-1 text-ink-muted transition-colors hover:bg-negative/10 hover:text-negative"
                          onClick={() => setConfirmDelete(k.uuid || k.id)}
                          type="button"
                        >
                          <Trash2 size={14} strokeWidth={2} />
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Inline add form */}
        {showForm === side && (
          <form
            className="mt-4 space-y-3 rounded-lg border border-accent/20 bg-accent/5 p-3"
            onSubmit={(e) => {
              e.preventDefault();
              handleCreate(market?.value);
            }}
          >
            <div>
              <label className="mb-1 block text-xs font-medium text-ink-muted">Access Key</label>
              <input
                autoFocus
                className="w-full rounded-md border border-border bg-background px-3 py-1.5 text-sm text-ink placeholder:text-ink-muted/50 focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent/30"
                onChange={(e) => setFormData((prev) => ({ ...prev, access_key: e.target.value }))}
                placeholder="Access Key를 입력하세요"
                required
                type="text"
                value={formData.access_key}
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-ink-muted">Secret Key</label>
              <div className="relative">
                <input
                  className="w-full rounded-md border border-border bg-background px-3 py-1.5 pr-9 text-sm text-ink placeholder:text-ink-muted/50 focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent/30"
                  onChange={(e) => setFormData((prev) => ({ ...prev, secret_key: e.target.value }))}
                  placeholder="Secret Key를 입력하세요"
                  required
                  type={showSecret ? "text" : "password"}
                  value={formData.secret_key}
                />
                <button
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-ink-muted hover:text-ink"
                  onClick={() => setShowSecret((v) => !v)}
                  type="button"
                >
                  {showSecret ? <EyeOff size={15} /> : <Eye size={15} />}
                </button>
              </div>
            </div>
            {isOkx && (
              <div>
                <label className="mb-1 block text-xs font-medium text-ink-muted">Passphrase</label>
                <div className="relative">
                  <input
                    className="w-full rounded-md border border-border bg-background px-3 py-1.5 pr-9 text-sm text-ink placeholder:text-ink-muted/50 focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent/30"
                    onChange={(e) => setFormData((prev) => ({ ...prev, passphrase: e.target.value }))}
                    placeholder="Passphrase를 입력하세요"
                    type={showPassphrase ? "text" : "password"}
                    value={formData.passphrase}
                  />
                  <button
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-ink-muted hover:text-ink"
                    onClick={() => setShowPassphrase((v) => !v)}
                    type="button"
                  >
                    {showPassphrase ? <EyeOff size={15} /> : <Eye size={15} />}
                  </button>
                </div>
              </div>
            )}
            <div className="flex items-center justify-end gap-2 pt-1">
              <button
                className="rounded-md px-3 py-1.5 text-xs font-semibold text-ink-muted transition-colors hover:bg-surface-elevated"
                onClick={() => setShowForm(null)}
                type="button"
              >
                취소
              </button>
              <button
                className="rounded-md bg-accent px-3 py-1.5 text-xs font-semibold text-white transition-colors hover:bg-accent/90 disabled:opacity-50"
                disabled={submitting || !formData.access_key || !formData.secret_key}
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

  return (
    <div className="space-y-4 p-4">
      <h3 className="text-sm font-semibold text-ink">API 키 관리</h3>

      {/* Node IP whitelist notice */}
      {nodeIp && (
        <div className="rounded-lg border border-accent/20 bg-accent/5 px-4 py-3">
          <p className="text-xs leading-relaxed text-ink-muted">
            거래소 API 설정에서 아래 IP를 허용 목록에 추가하세요:{" "}
            <code className="rounded bg-surface-elevated px-1.5 py-0.5 font-mono text-xs font-semibold text-ink">
              {nodeIp}
            </code>
          </p>
        </div>
      )}

      {/* 2-column grid */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {renderKeyTable("target", targetMarket, targetKeys)}
        {renderKeyTable("origin", originMarket, originKeys)}
      </div>
    </div>
  );
}
