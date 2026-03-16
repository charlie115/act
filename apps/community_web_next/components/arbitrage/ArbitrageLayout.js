import Link from "next/link";
import { ArrowLeftRight, TrendingUp } from "lucide-react";

const TABS = [
  { key: "diff", label: "펀딩비 차이", href: "/arbitrage/funding-rate/diff", icon: ArrowLeftRight },
  { key: "avg", label: "평균 펀딩비", href: "/arbitrage/funding-rate/avg", icon: TrendingUp },
];

export default function ArbitrageLayout({ currentTab, children }) {
  return (
    <div className="grid gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-lg font-bold text-ink">펀딩비 탐색</h1>
        <div className="flex rounded-lg border border-border bg-background/70 p-0.5">
          {TABS.map((tab) => {
            const active = currentTab === tab.key;
            const Icon = tab.icon;
            return (
              <Link
                key={tab.key}
                className={`inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-bold transition-all ${
                  active
                    ? "bg-accent/15 text-accent shadow-sm"
                    : "text-ink-muted hover:text-ink"
                }`}
                href={tab.href}
              >
                <Icon size={13} strokeWidth={2} />
                {tab.label}
              </Link>
            );
          })}
        </div>
      </div>
      {children}
    </div>
  );
}
