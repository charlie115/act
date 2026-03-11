"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";

import { useAuth } from "../auth/AuthProvider";

function formatDate(value) {
  if (!value) {
    return "-";
  }

  return new Intl.DateTimeFormat("ko-KR", {
    dateStyle: "long",
  }).format(new Date(value));
}

function formatAmount(value, maximumFractionDigits = 2) {
  const numberValue = Number(value || 0);

  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits,
    minimumFractionDigits: 0,
  }).format(numberValue);
}

function InfoRow({ label, value, action }) {
  return (
    <div className="profile-panel__row">
      <div>
        <p className="profile-panel__label">{label}</p>
        <strong>{value}</strong>
      </div>
      {action || null}
    </div>
  );
}

export default function MyPageClient() {
  const { authorizedListRequest, authorizedRequest, error, updateUser, user } = useAuth();
  const [pageError, setPageError] = useState("");
  const [isBusy, setIsBusy] = useState(false);
  const [referrals, setReferrals] = useState([]);
  const [feeLevel, setFeeLevel] = useState(null);
  const [depositBalance, setDepositBalance] = useState(null);
  const [referralCodeInput, setReferralCodeInput] = useState("");

  useEffect(() => {
    let active = true;

    async function loadPage() {
      setPageError("");

      try {
        const [nextReferrals, nextFeeLevels, nextDepositBalance] = await Promise.all([
          authorizedListRequest("/referral/referrals/"),
          authorizedListRequest("/fee/user-feelevel/"),
          authorizedListRequest("/users/deposit-balance/"),
        ]);

        if (!active) {
          return;
        }

        setReferrals(nextReferrals);
        setFeeLevel(nextFeeLevels[0] || null);
        setDepositBalance(nextDepositBalance[0] || null);
      } catch (requestError) {
        if (!active) {
          return;
        }

        setPageError(requestError.message || "Failed to load account details.");
      }
    }

    loadPage();

    return () => {
      active = false;
    };
  }, [authorizedListRequest]);

  const referralInfo = referrals[0] || null;
  const telegramBot = useMemo(
    () => user?.socialapps?.find((item) => item.provider === "telegram"),
    [user]
  );

  async function handleReferralSubmit(event) {
    event.preventDefault();

    if (!referralCodeInput) {
      return;
    }

    setIsBusy(true);
    setPageError("");

    try {
      const payload = await authorizedRequest("/referral/referrals/", {
        method: "POST",
        body: { referral_code: referralCodeInput },
      });

      setReferrals((current) => current.concat(payload));
      setReferralCodeInput("");
    } catch (requestError) {
      setPageError(requestError.payload?.message || "Failed to register referral code.");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleUnbindTelegram() {
    setIsBusy(true);
    setPageError("");

    try {
      await authorizedRequest("/users/users/unbind-telegram/", {
        method: "POST",
      });
      updateUser({ telegram_chat_id: "", socialapps: user?.socialapps?.filter((item) => item.provider !== "telegram") || [] });
    } catch (requestError) {
      setPageError(requestError.payload?.detail || "Failed to remove Telegram connection.");
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <div className="section-stack">
      <section className="surface-card">
        <div className="section-heading">
          <div>
            <p className="eyebrow">My Page</p>
            <h1>계정 개요</h1>
          </div>
          <Link className="ghost-button" href="/request-affiliate">
            Affiliate 신청
          </Link>
        </div>
        <div className="profile-panel">
          <InfoRow label="Username" value={user?.username || "-"} />
          <InfoRow label="Email" value={user?.email || "-"} />
          <InfoRow label="Joined" value={formatDate(user?.date_joined)} />
          <InfoRow
            label="Deposit Balance"
            value={
              depositBalance
                ? `${formatAmount(depositBalance.balance)} USDT`
                : "No balance data"
            }
            action={
              <Link className="ghost-button" href="/bot/deposit">
                Deposit
              </Link>
            }
          />
          <InfoRow
            label="Withdrawable Balance"
            value={
              depositBalance
                ? `${formatAmount(depositBalance.withdrawable_balance)} USDT`
                : "-"
            }
          />
          <InfoRow
            label="Fee Level"
            value={
              feeLevel
                ? `${feeLevel.fee_level} (${formatAmount(Number(feeLevel.fee_rate) * 100, 1)}%)`
                : "No fee level data"
            }
          />
        </div>
      </section>

      <section className="two-column-grid">
        <section className="surface-card">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Referral</p>
              <h2>추천 코드 등록</h2>
            </div>
          </div>
          {referralInfo ? (
            <div className="inline-note">
              현재 등록된 추천 코드: <strong>{referralInfo.referral_code}</strong>
            </div>
          ) : (
            <form className="auth-form" onSubmit={handleReferralSubmit}>
              <input
                className="auth-form__input"
                onChange={(event) => setReferralCodeInput(event.target.value)}
                placeholder="Enter referral code"
                value={referralCodeInput}
              />
              <button
                className="primary-button auth-button"
                disabled={!referralCodeInput || isBusy}
                type="submit"
              >
                {isBusy ? "Registering..." : "Register"}
              </button>
            </form>
          )}
        </section>

        <section className="surface-card">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Telegram</p>
              <h2>텔레그램 연결</h2>
            </div>
          </div>
          {user?.telegram_chat_id ? (
            <div className="auth-form">
              <div className="inline-note">
                <strong>{telegramBot?.client_id || "Telegram bot"}</strong> 와 연결되어 있습니다.
              </div>
              <button
                className="ghost-button ghost-button--button auth-button"
                disabled={isBusy}
                onClick={handleUnbindTelegram}
                type="button"
              >
                {isBusy ? "Disconnecting..." : "Disconnect Telegram"}
              </button>
            </div>
          ) : (
            <div className="inline-note">
              아직 텔레그램이 연결되지 않았습니다. 기존 봇 흐름 이전 전까지는 레거시 화면에서 연결을 유지해야 합니다.
            </div>
          )}
        </section>
      </section>

      <section className="surface-card">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Fee Details</p>
            <h2>수수료 진행 상황</h2>
          </div>
        </div>
        {feeLevel ? (
          <div className="profile-panel">
            <InfoRow
              label="Realtime Total Paid Fee"
              value={`${formatAmount(feeLevel.realtime_total_paid_fee)} USDT`}
            />
            <InfoRow
              label="Required Fee to Next Level"
              value={`${formatAmount(feeLevel.required_paid_fee_to_next_level)} USDT`}
            />
            <InfoRow
              label="Withdrawable Commission"
              value={
                depositBalance
                  ? `${formatAmount(depositBalance.withdrawable_commission)} USDT`
                  : "-"
              }
            />
          </div>
        ) : (
          <div className="empty-state">수수료 레벨 데이터를 불러오지 못했습니다.</div>
        )}
      </section>

      {pageError || error ? <p className="auth-card__error">{pageError || error}</p> : null}
    </div>
  );
}
