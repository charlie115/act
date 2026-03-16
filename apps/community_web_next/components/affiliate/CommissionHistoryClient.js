"use client";

import { useEffect, useMemo, useState } from "react";

import { useAuth } from "../auth/AuthProvider";

function formatAmount(value, maximumFractionDigits = 8) {
  const numberValue = Number(value || 0);

  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits,
    minimumFractionDigits: 0,
  }).format(numberValue);
}

export default function CommissionHistoryClient() {
  const { authorizedListRequest, user } = useAuth();
  const affiliate = user?.affiliate || null;
  const [commissionHistory, setCommissionHistory] = useState([]);
  const [subAffiliates, setSubAffiliates] = useState([]);
  const [filterAffiliateId, setFilterAffiliateId] = useState("all");
  const [orderBy, setOrderBy] = useState("created_at");
  const [order, setOrder] = useState("desc");
  const [pageError, setPageError] = useState("");

  useEffect(() => {
    let active = true;

    async function loadPage() {
      setPageError("");

      try {
        const [nextHistory, nextSubAffiliates] = await Promise.all([
          authorizedListRequest("/referral/commission-history/"),
          authorizedListRequest("/referral/sub-affiliate/"),
        ]);

        if (!active) {
          return;
        }

        setCommissionHistory(nextHistory);
        setSubAffiliates(nextSubAffiliates);
      } catch (requestError) {
        if (!active) {
          return;
        }

        setPageError(requestError.message || "정산 내역을 불러오지 못했습니다.");
      }
    }

    loadPage();

    return () => {
      active = false;
    };
  }, [authorizedListRequest]);

  const affiliateNameMap = useMemo(() => {
    const map = {};

    if (affiliate?.id) {
      map[affiliate.id] = "본인";
    }

    subAffiliates.forEach((subAffiliate) => {
      map[subAffiliate.id] = subAffiliate.user;
    });

    return map;
  }, [affiliate, subAffiliates]);

  const affiliateTierMap = useMemo(() => {
    const map = {};

    if (affiliate?.id) {
      map[affiliate.id] = affiliate.tier;
    }

    subAffiliates.forEach((subAffiliate) => {
      map[subAffiliate.id] = subAffiliate.tier;
    });

    return map;
  }, [affiliate, subAffiliates]);

  const filteredHistory = useMemo(() => {
    let records = [...commissionHistory];

    if (filterAffiliateId === "self") {
      records = records.filter((item) => item.affiliate === affiliate?.id);
    } else if (filterAffiliateId !== "all") {
      records = records.filter((item) => String(item.affiliate) === filterAffiliateId);
    }

    records.sort((left, right) => {
      let comparison = 0;

      if (orderBy === "created_at") {
        comparison = new Date(left.created_at) - new Date(right.created_at);
      } else if (orderBy === "change") {
        comparison = Number(left.change) - Number(right.change);
      }

      return order === "asc" ? comparison : -comparison;
    });

    return records;
  }, [affiliate, commissionHistory, filterAffiliateId, order, orderBy]);

  const totalCommission = useMemo(
    () =>
      filteredHistory.reduce((sum, record) => {
        if (record.type !== "COMMISSION") {
          return sum;
        }

        return sum + Number(record.change || 0);
      }, 0),
    [filteredHistory]
  );

  function toggleSort(field) {
    if (field === orderBy) {
      setOrder((current) => (current === "asc" ? "desc" : "asc"));
      return;
    }

    setOrderBy(field);
    setOrder("asc");
  }

  return (
    <div className="grid gap-4">
      <div className="rounded-lg border border-border bg-background/92 p-4">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          <h2 className="text-sm font-bold text-ink">커미션 정산 내역</h2>
          <div className="flex items-center gap-1">
            <button
              className={`rounded-md px-2.5 py-1 text-xs font-bold transition-colors ${
                filterAffiliateId === "all" ? "bg-accent/15 text-accent" : "text-ink-muted hover:bg-surface-elevated/40 hover:text-ink"
              }`}
              onClick={() => setFilterAffiliateId("all")}
              type="button"
            >
              전체
            </button>
            <button
              className={`rounded-md px-2.5 py-1 text-xs font-bold transition-colors ${
                filterAffiliateId === "self" ? "bg-accent/15 text-accent" : "text-ink-muted hover:bg-surface-elevated/40 hover:text-ink"
              }`}
              onClick={() => setFilterAffiliateId("self")}
              type="button"
            >
              본인
            </button>
            {subAffiliates.map((sub) => (
              <button
                key={sub.id}
                className={`rounded-md px-2.5 py-1 text-xs font-bold transition-colors ${
                  filterAffiliateId === String(sub.id) ? "bg-accent/15 text-accent" : "text-ink-muted hover:bg-surface-elevated/40 hover:text-ink"
                }`}
                onClick={() => setFilterAffiliateId(String(sub.id))}
                type="button"
              >
                {sub.user}
              </button>
            ))}
          </div>
        </div>
        <div className="overflow-x-auto rounded-lg border border-border bg-background/90">
          <table className="w-full border-collapse">
            <thead>
              <tr className="border-b border-border">
                <th className="px-3 py-2 text-left text-[0.62rem] font-bold uppercase tracking-widest text-ink-muted">제휴사</th>
                <th className="px-3 py-2 text-left text-[0.62rem] font-bold uppercase tracking-widest text-ink-muted">등급</th>
                <th className="px-3 py-2 text-left text-[0.62rem] font-bold uppercase tracking-widest text-ink-muted">유형</th>
                <th className="px-3 py-2 text-right text-[0.62rem] font-bold uppercase tracking-widest text-ink-muted">
                  <button className="hover:text-ink transition-colors" onClick={() => toggleSort("change")} type="button">
                    변동액 {orderBy === "change" ? (order === "asc" ? "↑" : "↓") : ""}
                  </button>
                </th>
                <th className="px-3 py-2 text-left text-[0.62rem] font-bold uppercase tracking-widest text-ink-muted">
                  <button className="hover:text-ink transition-colors" onClick={() => toggleSort("created_at")} type="button">
                    일시 {orderBy === "created_at" ? (order === "asc" ? "↑" : "↓") : ""}
                  </button>
                </th>
                <th className="px-3 py-2 text-left text-[0.62rem] font-bold uppercase tracking-widest text-ink-muted">서비스</th>
                <th className="px-3 py-2 text-left text-[0.62rem] font-bold uppercase tracking-widest text-ink-muted">거래 ID</th>
              </tr>
            </thead>
            <tbody>
              {filteredHistory.length ? (
                filteredHistory.map((record) => (
                  <tr key={record.id} className="border-t border-border/50 transition-colors hover:bg-surface-elevated/30">
                    <td className="px-3 py-2 text-sm text-ink">{affiliateNameMap[record.affiliate] || record.affiliate}</td>
                    <td className="px-3 py-2 text-xs text-ink-muted">{affiliateTierMap[record.affiliate] || "-"}</td>
                    <td className="px-3 py-2 text-xs text-ink-muted">{record.type}</td>
                    <td className="tabular-nums px-3 py-2 text-right font-mono text-sm text-ink">{formatAmount(record.change)}</td>
                    <td className="px-3 py-2 text-xs text-ink-muted">{new Date(record.created_at).toLocaleString()}</td>
                    <td className="px-3 py-2 text-xs text-ink-muted">{record.service_type || "-"}</td>
                    <td className="px-3 py-2 font-mono text-[0.68rem] text-ink-muted">{record.trade_uuid || "-"}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="7" className="px-4 py-8 text-center text-sm text-ink-muted">
                    정산 내역이 없습니다.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="rounded-lg border border-border bg-background/92 p-4">
        <h2 className="mb-2 text-sm font-bold text-ink">정산 합계</h2>
        <p className="text-sm text-ink-muted">
          총 정산 커미션: <strong className="text-ink">{formatAmount(totalCommission)}</strong>
        </p>
      </div>

      {pageError ? <p className="mt-3 text-sm text-negative">{pageError}</p> : null}
    </div>
  );
}
