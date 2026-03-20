"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { ChevronLeft, ChevronRight, Copy, Wallet } from "lucide-react";
import { toast } from "sonner";
import { useAuth } from "../auth/AuthProvider";

/* ------------------------------------------------------------------ */
/*  Constants                                                          */
/* ------------------------------------------------------------------ */

const TH =
  "sticky top-0 z-[1] px-2 py-2 sm:px-3 text-[0.5rem] sm:text-[0.65rem] font-bold uppercase tracking-wider text-ink-muted bg-[rgba(10,16,28,0.95)] backdrop-blur-sm whitespace-nowrap";
const TD = "px-2 py-1.5 sm:px-3 sm:py-2 whitespace-nowrap";
const TDM = `${TD} tabular-nums`;

const PAGE_SIZE = 20;

const TABS = [
  { key: "deposit", label: "입금" },
  { key: "withdraw", label: "출금" },
  { key: "history", label: "내역" },
];

const fmt = new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 });

function fmtNum(v) {
  if (v == null || v === "") return "-";
  return fmt.format(Number(v));
}

function fmtDate(v) {
  if (!v) return "-";
  const d = new Date(v);
  if (Number.isNaN(d.getTime())) return "-";
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function truncateAddress(addr) {
  if (!addr || addr.length <= 12) return addr || "-";
  return `${addr.slice(0, 6)}...${addr.slice(-6)}`;
}

const HISTORY_TYPE_COLOR = {
  DEPOSIT: "text-positive",
  COMMISSION: "text-positive",
  COUPON: "text-positive",
  FEE: "text-negative",
  TRANSFER: "text-negative",
  WITHDRAW: "text-negative",
};

const WITHDRAWAL_STATUS_STYLE = {
  PENDING: "bg-amber-500/15 text-amber-400",
  APPROVED: "bg-accent/15 text-accent",
  REJECTED: "bg-negative/15 text-negative",
  COMPLETED: "bg-positive/15 text-positive",
};

const WITHDRAWAL_STATUS_LABEL = {
  PENDING: "대기",
  APPROVED: "승인",
  REJECTED: "거절",
  COMPLETED: "완료",
};

/* ------------------------------------------------------------------ */
/*  Shimmer skeleton                                                   */
/* ------------------------------------------------------------------ */

const WIDTHS = ["45%", "55%", "65%", "70%", "60%", "50%"];

function SkeletonRows({ cols }) {
  return Array.from({ length: 6 }).map((_, i) => (
    <tr key={i} className="border-b border-border/10">
      {Array.from({ length: cols }).map((_, j) => (
        <td key={j} className={TD}>
          <div
            className="h-3 rounded-sm"
            style={{
              width: WIDTHS[(i * cols + j) % WIDTHS.length],
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
/*  Main component                                                     */
/* ------------------------------------------------------------------ */

export default function BotDepositClient() {
  const { authorizedRequest, user } = useAuth();
  const [activeTab, setActiveTab] = useState("deposit");

  /* ---------- Deposit tab state ------------------------------------ */
  const [address, setAddress] = useState("");
  const [addressLoading, setAddressLoading] = useState(true);
  const [checkCooldown, setCheckCooldown] = useState(0);
  const [checking, setChecking] = useState(false);

  /* ---------- Withdraw tab state ----------------------------------- */
  const [balanceData, setBalanceData] = useState(null);
  const [balanceLoading, setBalanceLoading] = useState(true);
  const [withdrawType, setWithdrawType] = useState("DEPOSIT");
  const [withdrawAmount, setWithdrawAmount] = useState("");
  const [withdrawAddress, setWithdrawAddress] = useState("");
  const [withdrawSubmitting, setWithdrawSubmitting] = useState(false);
  const [withdrawRequests, setWithdrawRequests] = useState([]);
  const [withdrawRequestsLoading, setWithdrawRequestsLoading] = useState(true);

  /* ---------- History tab state ------------------------------------ */
  const [history, setHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [historyPage, setHistoryPage] = useState(0);

  /* ================================================================ */
  /*  Data fetching                                                    */
  /* ================================================================ */

  /* --- Deposit address --- */
  useEffect(() => {
    if (!user?.uuid) return;
    let active = true;

    async function loadAddress() {
      setAddressLoading(true);
      try {
        const data = await authorizedRequest(`/wallet/address/${user.uuid}/`);
        if (active) setAddress(data?.address || "");
      } catch {
        if (active) setAddress("");
      } finally {
        if (active) setAddressLoading(false);
      }
    }

    loadAddress();
    return () => { active = false; };
  }, [user?.uuid, authorizedRequest]);

  /* --- Balance --- */
  const fetchBalance = useCallback(async () => {
    try {
      const data = await authorizedRequest("/users/deposit-balance/");
      setBalanceData(data);
    } catch {
      // ignore
    } finally {
      setBalanceLoading(false);
    }
  }, [authorizedRequest]);

  useEffect(() => {
    if (activeTab !== "withdraw") return;
    let active = true;
    setBalanceLoading(true);
    fetchBalance().then(() => {
      if (!active) return;
    });
    return () => { active = false; };
  }, [activeTab, fetchBalance]);

  /* --- Withdrawal requests --- */
  const fetchWithdrawRequests = useCallback(async () => {
    try {
      const data = await authorizedRequest("/users/withdrawal-request/");
      const results = Array.isArray(data) ? data : data?.results || [];
      setWithdrawRequests(results);
    } catch {
      setWithdrawRequests([]);
    } finally {
      setWithdrawRequestsLoading(false);
    }
  }, [authorizedRequest]);

  useEffect(() => {
    if (activeTab !== "withdraw") return;
    let active = true;
    setWithdrawRequestsLoading(true);
    fetchWithdrawRequests().then(() => {
      if (!active) return;
    });
    return () => { active = false; };
  }, [activeTab, fetchWithdrawRequests]);

  /* --- Deposit history --- */
  useEffect(() => {
    if (activeTab !== "history") return;
    let active = true;
    setHistoryLoading(true);

    async function loadHistory() {
      try {
        const data = await authorizedRequest("/users/deposit-history/");
        const results = Array.isArray(data) ? data : data?.results || [];
        if (active) {
          setHistory(results);
          setHistoryPage(0);
        }
      } catch {
        if (active) setHistory([]);
      } finally {
        if (active) setHistoryLoading(false);
      }
    }

    loadHistory();
    return () => { active = false; };
  }, [activeTab, authorizedRequest]);

  /* ================================================================ */
  /*  Handlers                                                         */
  /* ================================================================ */

  async function handleCopyAddress() {
    if (!address) return;
    try {
      await navigator.clipboard.writeText(address);
      toast.success("주소가 복사되었습니다");
    } catch {
      toast.error("복사 실패");
    }
  }

  async function handleCheckDeposit() {
    if (!user?.uuid || checking || checkCooldown > 0) return;
    setChecking(true);
    try {
      const data = await authorizedRequest("/wallet/transaction/", {
        method: "POST",
        body: { user: user.uuid, asset: "USDT" },
      });
      const amount = data?.result?.total_deposit_amount;
      toast.success(
        amount != null
          ? `입금 확인 완료 (총 입금: ${fmtNum(amount)} USDT)`
          : data?.message || "입금 확인 완료",
      );
    } catch {
      toast.error("입금 확인에 실패했습니다");
    } finally {
      setChecking(false);
      setCheckCooldown(5);
    }
  }

  // Cooldown timer
  useEffect(() => {
    if (checkCooldown <= 0) return;
    const timer = setTimeout(() => setCheckCooldown((c) => c - 1), 1000);
    return () => clearTimeout(timer);
  }, [checkCooldown]);

  async function handleWithdrawSubmit(e) {
    e.preventDefault();
    if (withdrawSubmitting) return;
    setWithdrawSubmitting(true);
    try {
      await authorizedRequest("/users/withdrawal-request/", {
        method: "POST",
        body: {
          amount: withdrawAmount,
          address: withdrawAddress,
          type: withdrawType,
        },
      });
      toast.success("출금 요청이 접수되었습니다");
      setWithdrawAmount("");
      setWithdrawAddress("");
      setWithdrawRequestsLoading(true);
      await fetchWithdrawRequests();
      await fetchBalance();
    } catch {
      toast.error("출금 요청에 실패했습니다");
    } finally {
      setWithdrawSubmitting(false);
    }
  }

  /* ================================================================ */
  /*  Derived values                                                   */
  /* ================================================================ */

  const maxWithdraw =
    withdrawType === "DEPOSIT"
      ? Number(balanceData?.withdrawable_balance) || 0
      : Number(balanceData?.withdrawable_commission) || 0;

  const sortedHistory = useMemo(
    () =>
      [...history].sort(
        (a, b) =>
          new Date(b.registered_datetime).getTime() -
          new Date(a.registered_datetime).getTime(),
      ),
    [history],
  );

  const historyTotalPages = Math.max(1, Math.ceil(sortedHistory.length / PAGE_SIZE));
  const historyPageRows = sortedHistory.slice(
    historyPage * PAGE_SIZE,
    (historyPage + 1) * PAGE_SIZE,
  );

  /* ================================================================ */
  /*  Render                                                           */
  /* ================================================================ */

  return (
    <div className="space-y-4 p-4">
      <h3 className="section-title">
        <Wallet size={15} strokeWidth={2} className="text-accent" />
        입출금
      </h3>

      {/* Tab bar */}
      <div className="flex rounded-lg border border-border bg-background/70 p-0.5">
        {TABS.map((tab) => {
          const active = activeTab === tab.key;
          return (
            <button
              key={tab.key}
              className={`inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-bold transition-all ${
                active
                  ? "bg-accent/15 text-accent shadow-sm"
                  : "text-ink-muted hover:text-ink"
              }`}
              onClick={() => setActiveTab(tab.key)}
              type="button"
            >
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Tab content */}
      {activeTab === "deposit" && (
        <DepositTab
          address={address}
          addressLoading={addressLoading}
          checkCooldown={checkCooldown}
          checking={checking}
          onCheckDeposit={handleCheckDeposit}
          onCopyAddress={handleCopyAddress}
        />
      )}

      {activeTab === "withdraw" && (
        <WithdrawTab
          balanceData={balanceData}
          balanceLoading={balanceLoading}
          maxWithdraw={maxWithdraw}
          onSubmit={handleWithdrawSubmit}
          setWithdrawAddress={setWithdrawAddress}
          setWithdrawAmount={setWithdrawAmount}
          setWithdrawType={setWithdrawType}
          withdrawAddress={withdrawAddress}
          withdrawAmount={withdrawAmount}
          withdrawRequests={withdrawRequests}
          withdrawRequestsLoading={withdrawRequestsLoading}
          withdrawSubmitting={withdrawSubmitting}
          withdrawType={withdrawType}
        />
      )}

      {activeTab === "history" && (
        <HistoryTab
          historyLoading={historyLoading}
          historyPage={historyPage}
          historyTotalPages={historyTotalPages}
          pageRows={historyPageRows}
          setHistoryPage={setHistoryPage}
          totalCount={sortedHistory.length}
        />
      )}
    </div>
  );
}

/* ================================================================== */
/*  Tab 1: Deposit                                                     */
/* ================================================================== */

function DepositTab({
  address,
  addressLoading,
  checkCooldown,
  checking,
  onCheckDeposit,
  onCopyAddress,
}) {
  if (addressLoading) {
    return (
      <div className="grid place-items-center py-12">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-border border-t-accent" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Address card */}
      <div className="rounded-lg border border-border/60 bg-background/80 p-4">
        <p className="mb-2 text-xs font-bold uppercase tracking-wider text-ink-muted">
          TRC-20 입금 주소
        </p>
        <div className="flex items-center gap-2">
          <code className="min-w-0 flex-1 truncate rounded-md border border-border bg-surface-elevated/30 px-3 py-2 font-mono text-sm text-ink">
            {address || "주소를 불러올 수 없습니다"}
          </code>
          {address && (
            <button
              className="inline-flex flex-shrink-0 items-center gap-1 rounded-md bg-accent/10 px-3 py-2 text-xs font-semibold text-accent transition-colors hover:bg-accent/20"
              onClick={onCopyAddress}
              type="button"
            >
              <Copy size={13} strokeWidth={2.5} />
              복사
            </button>
          )}
        </div>
        <p className="mt-3 text-[0.7rem] leading-relaxed text-ink-muted">
          TRC-20(USDT) 네트워크로만 입금해주세요. 다른 네트워크로 전송 시 자산이 유실될 수 있습니다.
        </p>
      </div>

      {/* Check deposit button */}
      <button
        className="w-full rounded-lg bg-accent px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-accent/90 disabled:opacity-50 disabled:cursor-not-allowed"
        disabled={checking || checkCooldown > 0}
        onClick={onCheckDeposit}
        type="button"
      >
        {checking
          ? "확인 중..."
          : checkCooldown > 0
            ? `입금 확인 (${checkCooldown}s)`
            : "입금 확인"}
      </button>
    </div>
  );
}

/* ================================================================== */
/*  Tab 2: Withdraw                                                    */
/* ================================================================== */

function WithdrawTab({
  balanceData,
  balanceLoading,
  maxWithdraw,
  onSubmit,
  setWithdrawAddress,
  setWithdrawAmount,
  setWithdrawType,
  withdrawAddress,
  withdrawAmount,
  withdrawRequests,
  withdrawRequestsLoading,
  withdrawSubmitting,
  withdrawType,
}) {
  return (
    <div className="space-y-4">
      {/* Balance cards */}
      {balanceLoading ? (
        <div className="grid place-items-center py-6">
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-border border-t-accent" />
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-2 sm:gap-3">
          <div className="rounded-lg border border-border/40 bg-surface-elevated/30 px-3 py-2.5">
            <p className="text-[0.55rem] sm:text-[0.65rem] font-bold uppercase tracking-wider text-ink-muted">
              예치금 잔액
            </p>
            <p className="mt-0.5 text-sm sm:text-base font-bold tabular-nums text-ink">
              {fmtNum(balanceData?.withdrawable_balance)} USDT
            </p>
          </div>
          <div className="rounded-lg border border-border/40 bg-surface-elevated/30 px-3 py-2.5">
            <p className="text-[0.55rem] sm:text-[0.65rem] font-bold uppercase tracking-wider text-ink-muted">
              커미션 잔액
            </p>
            <p className="mt-0.5 text-sm sm:text-base font-bold tabular-nums text-ink">
              {fmtNum(balanceData?.withdrawable_commission)} USDT
            </p>
          </div>
        </div>
      )}

      {/* Withdrawal form */}
      <form
        className="rounded-lg border border-border/60 bg-background/80 p-4 space-y-3"
        onSubmit={onSubmit}
      >
        <p className="text-xs font-bold uppercase tracking-wider text-ink-muted">
          출금 신청
        </p>

        {/* Type selector */}
        <div>
          <label className="mb-1 block text-xs font-medium text-ink-muted">유형</label>
          <div className="flex rounded-lg border border-border bg-background/70 p-0.5">
            <button
              className={`flex-1 rounded-md px-3 py-1.5 text-xs font-bold transition-all ${
                withdrawType === "DEPOSIT"
                  ? "bg-accent/15 text-accent shadow-sm"
                  : "text-ink-muted hover:text-ink"
              }`}
              onClick={() => setWithdrawType("DEPOSIT")}
              type="button"
            >
              예치금
            </button>
            <button
              className={`flex-1 rounded-md px-3 py-1.5 text-xs font-bold transition-all ${
                withdrawType === "COMMISSION"
                  ? "bg-accent/15 text-accent shadow-sm"
                  : "text-ink-muted hover:text-ink"
              }`}
              onClick={() => setWithdrawType("COMMISSION")}
              type="button"
            >
              커미션
            </button>
          </div>
        </div>

        {/* Amount */}
        <div>
          <label className="mb-1 flex items-center justify-between text-xs font-medium text-ink-muted">
            <span>금액 (USDT)</span>
            <span className="tabular-nums text-[0.65rem]">
              최대: {fmtNum(maxWithdraw)}
            </span>
          </label>
          <input
            className="w-full rounded-md border border-border bg-background px-3 py-1.5 text-sm text-ink placeholder:text-ink-muted/50 focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent/30"
            max={maxWithdraw}
            min={0}
            onChange={(e) => setWithdrawAmount(e.target.value)}
            placeholder="출금할 금액"
            required
            step="any"
            type="number"
            value={withdrawAmount}
          />
        </div>

        {/* Address */}
        <div>
          <label className="mb-1 block text-xs font-medium text-ink-muted">
            TRC-20 주소
          </label>
          <input
            className="w-full rounded-md border border-border bg-background px-3 py-1.5 text-sm text-ink placeholder:text-ink-muted/50 focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent/30"
            onChange={(e) => setWithdrawAddress(e.target.value)}
            placeholder="TRC-20 출금 주소"
            required
            type="text"
            value={withdrawAddress}
          />
        </div>

        {/* Submit */}
        <button
          className="w-full rounded-lg bg-accent px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-accent/90 disabled:opacity-50 disabled:cursor-not-allowed"
          disabled={
            withdrawSubmitting ||
            !withdrawAmount ||
            !withdrawAddress ||
            Number(withdrawAmount) <= 0 ||
            Number(withdrawAmount) > maxWithdraw
          }
          type="submit"
        >
          {withdrawSubmitting ? "요청 중..." : "출금 신청"}
        </button>
      </form>

      {/* Withdrawal requests table */}
      <div className="rounded-lg border border-border/60 bg-background/80 backdrop-blur-sm overflow-hidden">
        <div className="px-4 py-2.5 border-b border-border/40">
          <p className="text-xs font-bold uppercase tracking-wider text-ink-muted">
            출금 요청 내역
          </p>
        </div>
        {withdrawRequestsLoading ? (
          <div className="overflow-x-auto">
            <table className="w-full table-auto">
              <thead>
                <tr className="border-b border-border/40">
                  <th className={`${TH} text-left`}>유형</th>
                  <th className={`${TH} text-right`}>금액</th>
                  <th className={`${TH} text-left`}>주소</th>
                  <th className={`${TH} text-center`}>상태</th>
                  <th className={`${TH} text-left`}>요청일</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/20">
                <SkeletonRows cols={5} />
              </tbody>
            </table>
          </div>
        ) : withdrawRequests.length === 0 ? (
          <div className="flex flex-col items-center justify-center gap-3 py-12 text-ink-muted">
            <Wallet size={28} strokeWidth={1.5} className="text-ink-muted/30" />
            <p className="text-sm">출금 요청 내역이 없습니다.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full table-auto">
              <thead>
                <tr className="border-b border-border/40">
                  <th className={`${TH} text-left`}>유형</th>
                  <th className={`${TH} text-right`}>금액</th>
                  <th className={`${TH} text-left`}>주소</th>
                  <th className={`${TH} text-center`}>상태</th>
                  <th className={`${TH} text-left`}>요청일</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/20">
                {withdrawRequests.map((req) => (
                  <tr
                    key={req.id}
                    className="transition-colors duration-150 hover:bg-surface-elevated/60"
                  >
                    <td className={`${TD} text-left text-[0.72rem] sm:text-xs text-ink-muted`}>
                      {req.type === "DEPOSIT" ? "예치금" : "커미션"}
                    </td>
                    <td className={`${TDM} text-right text-[0.72rem] sm:text-xs text-ink`}>
                      {fmtNum(req.amount)}
                    </td>
                    <td className={`${TD} text-left font-mono text-[0.65rem] sm:text-xs text-ink-muted`}>
                      {truncateAddress(req.address)}
                    </td>
                    <td className={`${TD} text-center`}>
                      <span
                        className={`inline-block rounded-full px-2 py-0.5 text-[0.6rem] font-bold ${
                          WITHDRAWAL_STATUS_STYLE[req.status] || "bg-border/30 text-ink-muted"
                        }`}
                      >
                        {WITHDRAWAL_STATUS_LABEL[req.status] || req.status}
                      </span>
                    </td>
                    <td className={`${TDM} text-left text-[0.62rem] sm:text-xs text-ink-muted`}>
                      {fmtDate(req.requested_datetime)}
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

/* ================================================================== */
/*  Tab 3: History                                                     */
/* ================================================================== */

function HistoryTab({
  historyLoading,
  historyPage,
  historyTotalPages,
  pageRows,
  setHistoryPage,
  totalCount,
}) {
  return (
    <div className="space-y-4">
      <div className="rounded-lg border border-border/60 bg-background/80 backdrop-blur-sm overflow-hidden">
        {historyLoading ? (
          <div className="overflow-x-auto">
            <table className="w-full table-auto">
              <HistoryTableHead />
              <tbody className="divide-y divide-border/20">
                <SkeletonRows cols={5} />
              </tbody>
            </table>
          </div>
        ) : pageRows.length === 0 ? (
          <div className="flex flex-col items-center justify-center gap-3 py-16 text-ink-muted">
            <Wallet size={32} strokeWidth={1.5} className="text-ink-muted/30" />
            <p className="text-sm">거래 내역이 없습니다.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full table-auto">
              <HistoryTableHead />
              <tbody className="divide-y divide-border/20">
                {pageRows.map((row, i) => (
                  <tr
                    key={row.txid || `${row.registered_datetime}-${i}`}
                    className="transition-colors duration-150 hover:bg-surface-elevated/60"
                  >
                    <td className={`${TDM} text-right text-[0.72rem] sm:text-xs text-ink`}>
                      {fmtNum(row.balance)}
                    </td>
                    <td
                      className={`${TDM} text-right text-[0.72rem] sm:text-xs font-semibold ${
                        Number(row.change) >= 0 ? "text-positive" : "text-negative"
                      }`}
                    >
                      {Number(row.change) > 0 ? "+" : ""}
                      {fmtNum(row.change)}
                    </td>
                    <td className={`${TD} text-left font-mono text-[0.6rem] sm:text-[0.7rem] text-ink-muted`}>
                      {truncateAddress(row.txid)}
                    </td>
                    <td className={`${TD} text-center`}>
                      <span
                        className={`text-[0.68rem] font-bold ${
                          HISTORY_TYPE_COLOR[row.type] || "text-ink-muted"
                        }`}
                      >
                        {row.type}
                      </span>
                    </td>
                    <td className={`${TDM} text-left text-[0.62rem] sm:text-xs text-ink-muted`}>
                      {fmtDate(row.registered_datetime)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Pagination */}
      {!historyLoading && totalCount > PAGE_SIZE && (
        <div className="flex items-center justify-between px-1">
          <span className="text-[0.65rem] tabular-nums text-ink-muted">
            {historyPage * PAGE_SIZE + 1}&ndash;
            {Math.min((historyPage + 1) * PAGE_SIZE, totalCount)} / {totalCount}
          </span>
          <div className="flex items-center gap-1">
            <button
              className="inline-flex items-center justify-center rounded-md px-2 py-1 text-[0.65rem] font-semibold text-ink-muted transition-colors hover:bg-surface-elevated/60 disabled:opacity-30 disabled:cursor-not-allowed"
              disabled={historyPage === 0}
              onClick={() => setHistoryPage((p) => p - 1)}
              type="button"
            >
              <ChevronLeft size={14} strokeWidth={2} />
              이전
            </button>
            <span className="px-2 text-[0.65rem] tabular-nums text-ink-muted">
              {historyPage + 1} / {historyTotalPages}
            </span>
            <button
              className="inline-flex items-center justify-center rounded-md px-2 py-1 text-[0.65rem] font-semibold text-ink-muted transition-colors hover:bg-surface-elevated/60 disabled:opacity-30 disabled:cursor-not-allowed"
              disabled={historyPage >= historyTotalPages - 1}
              onClick={() => setHistoryPage((p) => p + 1)}
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

function HistoryTableHead() {
  return (
    <thead>
      <tr className="border-b border-border/40">
        <th className={`${TH} text-right`}>잔액</th>
        <th className={`${TH} text-right`}>변동</th>
        <th className={`${TH} text-left`}>TXID</th>
        <th className={`${TH} text-center`}>유형</th>
        <th className={`${TH} text-left`}>일시</th>
      </tr>
    </thead>
  );
}
