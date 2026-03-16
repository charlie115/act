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

function InfoRow({ label, value }) {
  return (
    <div className="profile-panel__row">
      <div>
        <p className="profile-panel__label">{label}</p>
        <strong>{value}</strong>
      </div>
    </div>
  );
}

export default function AffiliateDashboardClient() {
  const { authorizedListRequest, authorizedRequest, user } = useAuth();
  const [pageError, setPageError] = useState("");
  const [tiers, setTiers] = useState([]);
  const [referralCodes, setReferralCodes] = useState([]);
  const [subAffiliates, setSubAffiliates] = useState([]);
  const [isBusy, setIsBusy] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [form, setForm] = useState({
    code: "",
    user_discount_rate: 0.05,
  });

  useEffect(() => {
    let active = true;

    async function loadPage() {
      setPageError("");

      try {
        const [nextTiers, nextCodes, nextSubAffiliates] = await Promise.all([
          authorizedListRequest("/referral/affiliate-tier/"),
          authorizedListRequest("/referral/referral-code/"),
          authorizedListRequest("/referral/sub-affiliate/"),
        ]);

        if (!active) {
          return;
        }

        setTiers(nextTiers);
        setReferralCodes(nextCodes);
        setSubAffiliates(nextSubAffiliates);
      } catch (requestError) {
        if (!active) {
          return;
        }

        setPageError(requestError.message || "제휴 대시보드 로드에 실패했습니다.");
      }
    }

    loadPage();

    return () => {
      active = false;
    };
  }, [authorizedListRequest]);

  const affiliate = user?.affiliate;
  const userTier = useMemo(
    () => tiers.find((tier) => tier.id === affiliate?.tier) || null,
    [affiliate?.tier, tiers]
  );
  const parentCommissionRate = Number(userTier?.parent_commission_rate || 0);
  const selfCommissionRate = 1 - Number(form.user_discount_rate || 0);

  async function refreshCodes() {
    const nextCodes = await authorizedListRequest("/referral/referral-code/");
    setReferralCodes(nextCodes);
  }

  async function handleCreateCode(event) {
    event.preventDefault();
    setIsBusy(true);
    setPageError("");

    try {
      await authorizedRequest("/referral/referral-code/", {
        method: "POST",
        body: {
          code: form.code,
          user_discount_rate: Number(form.user_discount_rate),
        },
      });

      await refreshCodes();
      setIsModalOpen(false);
      setForm({ code: "", user_discount_rate: 0.05 });
    } catch (requestError) {
      setPageError(requestError.payload?.code?.[0] || "추천 코드 생성에 실패했습니다.");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleDeleteCode(id) {
    setIsBusy(true);
    setPageError("");

    try {
      await authorizedRequest(`/referral/referral-code/${id}/`, {
        method: "DELETE",
      });
      await refreshCodes();
    } catch (requestError) {
      setPageError(requestError.message || "추천 코드 삭제에 실패했습니다.");
    } finally {
      setIsBusy(false);
    }
  }

  if (!affiliate) {
    return <div className="empty-state">아직 제휴 계정이 아닙니다.</div>;
  }

  return (
    <div className="section-stack">
      <section className="surface-card">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Affiliate</p>
            <h1>제휴 수익 개요</h1>
          </div>
          <button className="primary-button ghost-button--button" onClick={() => setIsModalOpen(true)} type="button">
            추천 코드 생성
          </button>
        </div>
        <div className="profile-panel">
          <InfoRow label="등급" value={userTier?.name || "-"} />
          <InfoRow
            label="기본 수수료율"
            value={`${formatAmount(Number(userTier?.base_commission_rate || 0) * 100, 2)}%`}
          />
          <InfoRow label="제휴 코드" value={affiliate.affiliate_code || "-"} />
          <InfoRow
            label="직접 수수료"
            value={formatAmount(affiliate.total_direct_commission)}
          />
          <InfoRow
            label="하위 수수료"
            value={formatAmount(affiliate.total_forwarded_commission)}
          />
          <InfoRow
            label="총 수수료"
            value={formatAmount(affiliate.total_earned_commission)}
          />
        </div>
      </section>

      {parentCommissionRate > 0 ? (
        <section className="surface-card">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Sub Affiliates</p>
              <h2>하위 제휴 계정</h2>
            </div>
          </div>
          {subAffiliates.length ? (
            <div className="table-shell">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>사용자</th>
                    <th>등급</th>
                    <th>추천 수</th>
                    <th>총 수익</th>
                    <th>전달 수수료</th>
                    <th>생성일</th>
                  </tr>
                </thead>
                <tbody>
                  {subAffiliates.map((subAffiliate) => (
                    <tr key={subAffiliate.id}>
                      <td>{subAffiliate.user}</td>
                      <td>{subAffiliate.tier}</td>
                      <td>{subAffiliate.referral_count}</td>
                      <td>{formatAmount(subAffiliate.total_earned_commission)}</td>
                      <td>{formatAmount(subAffiliate.total_forwarding_commission)}</td>
                      <td>{new Date(subAffiliate.created_at).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="inline-note">하위 제휴 계정이 없습니다.</div>
          )}
        </section>
      ) : null}

      <section className="surface-card">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Referral Codes</p>
            <h2>추천 코드 관리</h2>
          </div>
        </div>
        <div className="table-shell">
          <table className="data-table">
            <thead>
              <tr>
                <th>코드</th>
                <th>사용자 할인</th>
                <th>자체 수수료</th>
                <th>추천 수</th>
                <th>총 수익</th>
                <th>생성일</th>
                <th>삭제</th>
              </tr>
            </thead>
            <tbody>
              {referralCodes.length ? (
                referralCodes.map((code) => (
                  <tr key={code.id}>
                    <td>{code.code}</td>
                    <td>{formatAmount(Number(code.user_discount_rate) * 100, 0)}%</td>
                    <td>{formatAmount(Number(code.self_commission_rate) * 100, 0)}%</td>
                    <td>{code.referral_count || 0}</td>
                    <td>{formatAmount(code.total_earned_commission)}</td>
                    <td>{new Date(code.created_at).toLocaleString()}</td>
                    <td>
                      <button
                        className="ghost-button ghost-button--button"
                        disabled={isBusy}
                        onClick={() => handleDeleteCode(code.id)}
                        type="button"
                      >
                        삭제
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="7">추천 코드가 없습니다.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      {isModalOpen ? (
        <div className="modal-backdrop" onClick={() => setIsModalOpen(false)} role="presentation">
          <div className="modal-card" onClick={(event) => event.stopPropagation()} role="dialog" aria-modal="true">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Create</p>
                <h2>추천 코드 생성</h2>
              </div>
            </div>
            <form className="auth-form" onSubmit={handleCreateCode}>
              <label className="auth-form__field" htmlFor="referral-code">
                코드
              </label>
              <input
                className="auth-form__input"
                id="referral-code"
                onChange={(event) => setForm((current) => ({ ...current, code: event.target.value }))}
                required
                value={form.code}
              />

              <label className="auth-form__field" htmlFor="discount-rate">
                사용자 할인율: {formatAmount(Number(form.user_discount_rate) * 100, 0)}%
              </label>
              <input
                id="discount-rate"
                max="1"
                min="0"
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    user_discount_rate: Number(event.target.value),
                  }))
                }
                step="0.01"
                type="range"
                value={form.user_discount_rate}
              />
              <div className="inline-note">
                자체 수수료율: {formatAmount(selfCommissionRate * 100, 0)}%
              </div>

              <div className="modal-card__actions">
                <button
                  className="ghost-button ghost-button--button"
                  onClick={() => setIsModalOpen(false)}
                  type="button"
                >
                  취소
                </button>
                <button className="primary-button ghost-button--button" disabled={isBusy} type="submit">
                  {isBusy ? "생성 중..." : "생성"}
                </button>
              </div>
            </form>
          </div>
        </div>
      ) : null}

      {pageError ? <p className="auth-card__error">{pageError}</p> : null}
    </div>
  );
}
