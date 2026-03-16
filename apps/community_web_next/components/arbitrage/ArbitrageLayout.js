import Link from "next/link";

export default function ArbitrageLayout({ currentTab, children }) {
  return (
    <div className="grid gap-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-lg font-bold text-ink">펀딩비 탐색</h1>
          <p className="mt-0.5 text-xs text-ink-muted">
            거래소 간 펀딩비 차이를 비교하고 평균 펀딩비를 확인합니다.
          </p>
        </div>
        <div className="flex gap-1">
          <Link
            className={`rounded-lg px-3 py-1.5 text-xs font-bold transition-colors ${
              currentTab === "diff"
                ? "bg-accent/15 text-accent"
                : "text-ink-muted hover:bg-surface-elevated/40 hover:text-ink"
            }`}
            href="/arbitrage/funding-rate/diff"
          >
            펀딩비 차이
          </Link>
          <Link
            className={`rounded-lg px-3 py-1.5 text-xs font-bold transition-colors ${
              currentTab === "avg"
                ? "bg-accent/15 text-accent"
                : "text-ink-muted hover:bg-surface-elevated/40 hover:text-ink"
            }`}
            href="/arbitrage/funding-rate/avg"
          >
            평균 펀딩비
          </Link>
        </div>
      </div>
      {children}
    </div>
  );
}
