"use client";

import { useEffect, useMemo, useState } from "react";

import { useAuth } from "../auth/AuthProvider";

function formatAmount(value, maximumFractionDigits = 2) {
  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits,
    minimumFractionDigits: 0,
  }).format(Number(value || 0));
}

function formatDate(value) {
  if (!value) {
    return "-";
  }

  return new Date(value).toLocaleString();
}

export default function BotDepositClient() {
  const { authorizedListRequest, authorizedRequest, user } = useAuth();
  const [walletAddress, setWalletAddress] = useState("");
  const [trxBalance, setTrxBalance] = useState(null);
  const [depositBalance, setDepositBalance] = useState(null);
  const [depositHistory, setDepositHistory] = useState([]);
  const [withdrawalHistory, setWithdrawalHistory] = useState([]);
  const [isBusy, setIsBusy] = useState(false);
  const [pageError, setPageError] = useState("");
  const [topUpResult, setTopUpResult] = useState(null);
  const [withdrawForm, setWithdrawForm] = useState({
    type: "DEPOSIT",
    amount: "",
    address: "",
  });

  useEffect(() => {
    let active = true;

    async function loadPage() {
      if (!user?.uuid) {
        return;
      }

      setPageError("");

      try {
        const [
          addressPayload,
          trxBalancePayload,
          nextDepositBalances,
          nextDepositHistory,
          nextWithdrawalHistory,
        ] = await Promise.all([
          authorizedRequest(`/wallet/address/${user.uuid}/`),
          authorizedRequest(`/wallet/balance/${user.uuid}/?asset=TRX`),
          authorizedListRequest("/users/deposit-balance/"),
          authorizedListRequest("/users/deposit-history/"),
          authorizedListRequest("/users/withdrawal-request/"),
        ]);

        if (!active) {
          return;
        }

        setWalletAddress(addressPayload?.address || "");
        setTrxBalance(trxBalancePayload?.balance ?? null);
        setDepositBalance(nextDepositBalances[0] || null);
        setDepositHistory(nextDepositHistory);
        setWithdrawalHistory(nextWithdrawalHistory);
      } catch (requestError) {
        if (!active) {
          return;
        }

        setPageError(requestError.message || "Failed to load deposit data.");
      }
    }

    loadPage();

    return () => {
      active = false;
    };
  }, [authorizedListRequest, authorizedRequest, user?.uuid]);

  const withdrawableAmount = useMemo(() => {
    if (!depositBalance) {
      return 0;
    }

    if (withdrawForm.type === "COMMISSION") {
      return Number(depositBalance.withdrawable_commission || 0);
    }

    return Number(depositBalance.withdrawable_balance || 0);
  }, [depositBalance, withdrawForm.type]);

  async function reloadHistory() {
    const [nextDepositBalances, nextDepositHistory, nextWithdrawalHistory] = await Promise.all([
      authorizedListRequest("/users/deposit-balance/"),
      authorizedListRequest("/users/deposit-history/"),
      authorizedListRequest("/users/withdrawal-request/"),
    ]);

    setDepositBalance(nextDepositBalances[0] || null);
    setDepositHistory(nextDepositHistory);
    setWithdrawalHistory(nextWithdrawalHistory);
  }

  async function handleCheckDeposit() {
    if (!user?.uuid) {
      return;
    }

    setIsBusy(true);
    setPageError("");

    try {
      const payload = await authorizedRequest("/wallet/transaction/", {
        method: "POST",
        body: {
          user: user.uuid,
          asset: "USDT",
        },
      });

      setTopUpResult(payload?.result || null);
      await reloadHistory();
    } catch (requestError) {
      setPageError(requestError.message || "Failed to check transactions.");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleWithdrawal(event) {
    event.preventDefault();

    setIsBusy(true);
    setPageError("");

    try {
      await authorizedRequest("/users/withdrawal-request/", {
        method: "POST",
        body: {
          type: withdrawForm.type,
          amount: Number(withdrawForm.amount),
          address: withdrawForm.address,
        },
      });

      setWithdrawForm({
        type: "DEPOSIT",
        amount: "",
        address: "",
      });

      await reloadHistory();
    } catch (requestError) {
      setPageError(requestError.payload?.detail || requestError.message || "Failed to request withdrawal.");
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <div className="section-stack">
      <section className="surface-card">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Deposit</p>
            <h1>입금 주소와 상태 확인</h1>
          </div>
        </div>
        <div className="auth-form">
          <div className="inline-note">
            ACW 지갑 주소
            <div className="mono-cell mono-cell--wrap">{walletAddress || "Loading..."}</div>
          </div>
          <div className="bot-inline-actions">
            <button
              className="ghost-button ghost-button--button"
              onClick={() => navigator.clipboard?.writeText(walletAddress)}
              type="button"
            >
              Copy Address
            </button>
            <button className="primary-button ghost-button--button" disabled={isBusy} onClick={handleCheckDeposit} type="button">
              {isBusy ? "Checking..." : "Check Transactions"}
            </button>
          </div>
          {topUpResult ? (
            <div className="profile-panel">
              <div className="profile-panel__row">
                <div>
                  <p className="profile-panel__label">Total Deposit Amount</p>
                  <strong>{formatAmount(topUpResult.total_deposit_amount)} USDT</strong>
                </div>
              </div>
              <div className="profile-panel__row">
                <div>
                  <p className="profile-panel__label">Current Balance</p>
                  <strong>{formatAmount(depositBalance?.balance)} USDT</strong>
                </div>
              </div>
            </div>
          ) : null}
        </div>
      </section>

      <section className="two-column-grid">
        <section className="surface-card">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Wallet</p>
              <h2>출금 가능 잔액</h2>
            </div>
          </div>
          <div className="profile-panel">
            <div className="profile-panel__row">
              <div>
                <p className="profile-panel__label">TRX Balance</p>
                <strong>{formatAmount(trxBalance, 4)} TRX</strong>
              </div>
            </div>
            <div className="profile-panel__row">
              <div>
                <p className="profile-panel__label">Withdrawable Deposit</p>
                <strong>{formatAmount(depositBalance?.withdrawable_balance)} USDT</strong>
              </div>
            </div>
            <div className="profile-panel__row">
              <div>
                <p className="profile-panel__label">Withdrawable Commission</p>
                <strong>{formatAmount(depositBalance?.withdrawable_commission)} USDT</strong>
              </div>
            </div>
          </div>
        </section>

        <section className="surface-card">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Withdrawal</p>
              <h2>출금 요청</h2>
            </div>
          </div>
          <form className="auth-form" onSubmit={handleWithdrawal}>
            <label className="auth-form__field" htmlFor="withdraw-type">
              Type
            </label>
            <select
              className="select-input"
              id="withdraw-type"
              onChange={(event) => setWithdrawForm((current) => ({ ...current, type: event.target.value }))}
              value={withdrawForm.type}
            >
              <option value="DEPOSIT">Deposit Balance</option>
              <option value="COMMISSION">Commission</option>
            </select>

            <label className="auth-form__field" htmlFor="withdraw-amount">
              Amount
            </label>
            <input
              className="auth-form__input"
              id="withdraw-amount"
              max={withdrawableAmount}
              min="1"
              onChange={(event) => setWithdrawForm((current) => ({ ...current, amount: event.target.value }))}
              required
              type="number"
              value={withdrawForm.amount}
            />

            <label className="auth-form__field" htmlFor="withdraw-address">
              Address
            </label>
            <input
              className="auth-form__input"
              id="withdraw-address"
              onChange={(event) => setWithdrawForm((current) => ({ ...current, address: event.target.value }))}
              required
              value={withdrawForm.address}
            />

            <div className="inline-note">
              Available to withdraw: <strong>{formatAmount(withdrawableAmount)} USDT</strong>
            </div>

            <button
              className="primary-button ghost-button--button auth-button"
              disabled={
                isBusy ||
                !withdrawForm.amount ||
                !withdrawForm.address ||
                Number(withdrawForm.amount) <= 0 ||
                Number(withdrawForm.amount) > withdrawableAmount
              }
              type="submit"
            >
              {isBusy ? "Submitting..." : "Request Withdrawal"}
            </button>
          </form>
        </section>
      </section>

      <section className="surface-card">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Deposit History</p>
            <h2>입금 내역</h2>
          </div>
        </div>
        <div className="table-shell">
          <table className="data-table">
            <thead>
              <tr>
                <th>Type</th>
                <th>Change</th>
                <th>Balance</th>
                <th>TXID</th>
                <th>Registered</th>
              </tr>
            </thead>
            <tbody>
              {depositHistory.length ? (
                depositHistory
                  .slice()
                  .sort((left, right) => new Date(right.registered_datetime) - new Date(left.registered_datetime))
                  .map((item, index) => (
                    <tr key={`${item.txid || item.registered_datetime}-${index}`}>
                      <td>{item.type}</td>
                      <td>{formatAmount(item.change)}</td>
                      <td>{formatAmount(item.balance)}</td>
                      <td className="mono-cell">{item.txid || "-"}</td>
                      <td>{formatDate(item.registered_datetime)}</td>
                    </tr>
                  ))
              ) : (
                <tr>
                  <td colSpan="5">No deposit history found.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      <section className="surface-card">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Withdrawal History</p>
            <h2>출금 요청 내역</h2>
          </div>
        </div>
        <div className="table-shell">
          <table className="data-table">
            <thead>
              <tr>
                <th>Type</th>
                <th>Amount</th>
                <th>Address</th>
                <th>Status</th>
                <th>Requested</th>
              </tr>
            </thead>
            <tbody>
              {withdrawalHistory.length ? (
                withdrawalHistory
                  .slice()
                  .sort((left, right) => new Date(right.requested_datetime) - new Date(left.requested_datetime))
                  .map((item) => (
                    <tr key={item.id}>
                      <td>{item.type}</td>
                      <td>{formatAmount(item.amount)}</td>
                      <td className="mono-cell mono-cell--wrap">{item.address}</td>
                      <td>{item.status}</td>
                      <td>{formatDate(item.requested_datetime)}</td>
                    </tr>
                  ))
              ) : (
                <tr>
                  <td colSpan="5">No withdrawal requests found.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      {pageError ? <p className="auth-card__error">{pageError}</p> : null}
    </div>
  );
}
