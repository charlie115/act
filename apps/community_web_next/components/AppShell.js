"use client";

import Link from "next/link";
import { useCallback, useMemo, useState } from "react";
import { usePathname } from "next/navigation";
import {
  Bot,
  LayoutDashboard,
  Menu,
  MessageSquareQuote,
  Newspaper,
  Percent,
  Sparkles,
  X,
} from "lucide-react";

import AuthActions from "./auth/AuthActions";
import NextBreadcrumbs from "./NextBreadcrumbs";
import ScrollToTop from "./ui/ScrollToTop";

const routeMeta = [
  {
    match: "/",
    label: "홈",
    icon: LayoutDashboard,
    description: "실시간 프리미엄 데이터와 시장 조합 탐색",
  },
  {
    match: "/news",
    label: "뉴스",
    icon: Newspaper,
    description: "뉴스, 공지, 소셜 신호 통합 피드",
  },
  {
    match: "/community-board",
    label: "게시판",
    icon: MessageSquareQuote,
    description: "커뮤니티 게시글과 토론",
  },
  {
    match: "/arbitrage",
    label: "아비트리지",
    icon: Percent,
    description: "펀딩비 비교 및 스프레드 분석",
  },
  {
    match: "/bot",
    label: "봇",
    icon: Bot,
    description: "봇 설정, 트리거, 스캐너 운영",
  },
  {
    match: "/coupon-dashboard",
    label: "쿠폰",
    icon: Sparkles,
    description: "추천, 쿠폰 및 제휴 운영",
  },
  {
    match: "/request-affiliate",
    label: "제휴",
    icon: Sparkles,
    description: "추천, 쿠폰 및 제휴 운영",
  },
  {
    match: "/affiliate",
    label: "제휴",
    icon: Sparkles,
    description: "추천, 쿠폰 및 제휴 운영",
  },
  {
    match: "/my-page",
    label: "마이페이지",
    icon: Sparkles,
    description: "프로필, 잔고, 계정 설정",
  },
];

export default function AppShell({ children }) {
  const pathname = usePathname();
  const [drawerOpen, setDrawerOpen] = useState(false);

  const currentMeta = useMemo(() => {
    const matched = routeMeta.find((item) =>
      item.match === "/" ? pathname === "/" : pathname.startsWith(item.match)
    );

    return matched || { label: "ArbiCrypto" };
  }, [pathname]);

  const closeDrawer = useCallback(() => setDrawerOpen(false), []);

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-20 mx-auto w-full rounded-none border-b border-border bg-background/94 backdrop-blur-lg md:top-1.5 md:w-[min(1280px,calc(100vw-20px))] md:rounded-xl md:border">
        <div className="relative z-1 mx-auto flex items-center justify-between gap-4 px-4 py-2 md:w-[min(1280px,calc(100vw-32px))]" style={{ minHeight: 56 }}>
          <div className="flex items-center gap-3 min-w-0">
            <Link className="inline-flex items-center gap-2 font-bold text-ink" href="/">
              <span className="inline-flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-accent to-sky-400 text-[0.78rem] font-mono text-white shadow-md">
                A
              </span>
              <span className="text-sm font-bold tracking-tight">ArbiCrypto</span>
            </Link>
          </div>

          {/* Desktop nav */}
          <nav className="hidden flex-1 items-center gap-0.5 overflow-x-auto md:flex" aria-label="Primary">
            {routeMeta.slice(0, 5).map((item) => {
              const active =
                item.match === "/"
                  ? pathname === "/"
                  : pathname.startsWith(item.match);
              const Icon = item.icon;

              return (
                <Link
                  key={item.match}
                  className={`inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-[0.8rem] font-semibold transition-colors ${
                    active
                      ? "bg-accent/20 text-ink shadow-[inset_0_0_0_1px_rgba(67,109,193,0.22)]"
                      : "text-ink-muted hover:bg-surface-elevated/60 hover:text-ink"
                  }`}
                  href={item.match}
                >
                  <Icon size={14} strokeWidth={2} />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>

          <div className="flex items-center gap-2">
            <div className="hidden md:flex">
              <AuthActions />
            </div>
            {/* Mobile hamburger */}
            <button
              aria-label="메뉴 열기"
              className="inline-flex h-9 w-9 items-center justify-center rounded-lg text-ink-muted transition-colors hover:bg-surface-elevated hover:text-ink md:hidden"
              onClick={() => setDrawerOpen(true)}
              type="button"
            >
              <Menu size={20} strokeWidth={2} />
            </button>
          </div>
        </div>
      </header>

      {/* Mobile drawer overlay */}
      {drawerOpen ? (
        <div className="fixed inset-0 z-50 md:hidden">
          <div
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={closeDrawer}
          />
          <nav className="absolute right-0 top-0 flex h-full w-[280px] max-w-[80vw] flex-col bg-background/98 shadow-2xl">
            <div className="flex items-center justify-between border-b border-border px-4 py-3">
              <span className="text-sm font-bold text-ink">메뉴</span>
              <button
                aria-label="메뉴 닫기"
                className="inline-flex h-8 w-8 items-center justify-center rounded-lg text-ink-muted transition-colors hover:bg-surface-elevated hover:text-ink"
                onClick={closeDrawer}
                type="button"
              >
                <X size={18} strokeWidth={2} />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto px-3 py-3">
              <div className="grid gap-1">
                {routeMeta.map((item) => {
                  const active =
                    item.match === "/"
                      ? pathname === "/"
                      : pathname.startsWith(item.match);
                  const Icon = item.icon;

                  return (
                    <Link
                      key={item.match}
                      className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-semibold transition-colors ${
                        active
                          ? "bg-accent/15 text-ink"
                          : "text-ink-muted hover:bg-surface-elevated/60 hover:text-ink"
                      }`}
                      href={item.match}
                      onClick={closeDrawer}
                    >
                      <Icon size={16} strokeWidth={2} />
                      <div>
                        <div>{item.label}</div>
                        <div className="text-[0.66rem] font-normal text-ink-muted">{item.description}</div>
                      </div>
                    </Link>
                  );
                })}
              </div>
            </div>
            <div className="border-t border-border px-4 py-3">
              <AuthActions />
            </div>
          </nav>
        </div>
      ) : null}

      <div className="mx-auto w-[min(1280px,calc(100vw-24px))] pt-2.5 pb-6">
        <NextBreadcrumbs />
      </div>
      <main className="mx-auto w-[min(1280px,calc(100vw-24px))] pb-8">{children}</main>
      <ScrollToTop />
    </div>
  );
}
