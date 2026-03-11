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

        setPageError(requestError.message || "Failed to load commission history.");
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
      map[affiliate.id] = "Self";
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
    <div className="section-stack">
      <section className="surface-card">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Commission History</p>
            <h1>커미션 정산 내역</h1>
          </div>
          <select
            className="select-input"
            onChange={(event) => setFilterAffiliateId(event.target.value)}
            value={filterAffiliateId}
          >
            <option value="all">All affiliates</option>
            <option value="self">Self</option>
            {subAffiliates.map((subAffiliate) => (
              <option key={subAffiliate.id} value={String(subAffiliate.id)}>
                {subAffiliate.user}
              </option>
            ))}
          </select>
        </div>
        <div className="table-shell">
          <table className="data-table">
            <thead>
              <tr>
                <th>Affiliate</th>
                <th>Tier</th>
                <th>Type</th>
                <th>
                  <button className="table-sort" onClick={() => toggleSort("change")} type="button">
                    Change
                  </button>
                </th>
                <th>
                  <button className="table-sort" onClick={() => toggleSort("created_at")} type="button">
                    Created At
                  </button>
                </th>
                <th>Service Type</th>
                <th>Trade UUID</th>
              </tr>
            </thead>
            <tbody>
              {filteredHistory.length ? (
                filteredHistory.map((record) => (
                  <tr key={record.id}>
                    <td>{affiliateNameMap[record.affiliate] || record.affiliate}</td>
                    <td>{affiliateTierMap[record.affiliate] || "-"}</td>
                    <td>{record.type}</td>
                    <td>{formatAmount(record.change)}</td>
                    <td>{new Date(record.created_at).toLocaleString()}</td>
                    <td>{record.service_type || "-"}</td>
                    <td className="mono-cell">{record.trade_uuid || "-"}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="7">No commission history found.</td>
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
            <h2>필터 기준 커미션 합계</h2>
          </div>
        </div>
        <div className="inline-note">
          Total earned commission: <strong>{formatAmount(totalCommission)}</strong>
        </div>
      </section>

      {pageError ? <p className="auth-card__error">{pageError}</p> : null}
    </div>
  );
}
