"use client";

import Link from "next/link";

const NAV_LINKS = [
  { href: "/", label: "홈" },
  { href: "/news", label: "뉴스" },
  { href: "/community-board", label: "게시판" },
  { href: "/arbitrage", label: "아비트리지" },
  { href: "/bot", label: "봇" },
];

const LEGAL_LINKS = [
  { href: "/terms", label: "이용약관" },
  { href: "/privacy", label: "개인정보처리방침" },
];

export default function Footer() {
  return (
    <footer className="mt-12 border-t border-border bg-background/98">
      <div className="mx-auto w-[min(1280px,calc(100vw-24px))] py-8">
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {/* Brand */}
          <div>
            <div className="mb-3 flex items-center gap-2">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img alt="ArbiCrypto" className="h-6 w-auto" src="/images/logo-no-background.png" />
            </div>
            <p className="text-[0.78rem] leading-relaxed text-ink-muted">
              실시간 김프·프리미엄 데이터와 아비트리지 분석 플랫폼
            </p>
          </div>

          {/* Navigation */}
          <div>
            <h3 className="mb-2.5 text-[0.62rem] font-bold uppercase tracking-[0.14em] text-accent">서비스</h3>
            <nav className="grid gap-1.5">
              {NAV_LINKS.map((link) => (
                <Link
                  key={link.href}
                  className="text-[0.78rem] text-ink-muted transition-colors hover:text-ink"
                  href={link.href}
                >
                  {link.label}
                </Link>
              ))}
            </nav>
          </div>

          {/* Legal */}
          <div>
            <h3 className="mb-2.5 text-[0.62rem] font-bold uppercase tracking-[0.14em] text-accent">법적 고지</h3>
            <nav className="grid gap-1.5">
              {LEGAL_LINKS.map((link) => (
                <Link
                  key={link.href}
                  className="text-[0.78rem] text-ink-muted transition-colors hover:text-ink"
                  href={link.href}
                >
                  {link.label}
                </Link>
              ))}
            </nav>
          </div>

          {/* Disclaimer */}
          <div>
            <h3 className="mb-2.5 text-[0.62rem] font-bold uppercase tracking-[0.14em] text-accent">면책사항</h3>
            <p className="text-[0.72rem] leading-relaxed text-ink-muted/70">
              본 서비스는 정보 제공 목적이며 투자 조언을 구성하지 않습니다. 암호화폐 거래는 원금 손실 위험이 있습니다.
            </p>
          </div>
        </div>

        <div className="mt-8 flex flex-wrap items-center justify-between gap-3 border-t border-border/50 pt-4">
          <span className="text-[0.68rem] text-ink-muted/60">
            © {new Date().getFullYear()} ArbiCrypto. All rights reserved.
          </span>
          <span className="text-[0.62rem] font-mono text-ink-muted/40">v0.1.0</span>
        </div>
      </div>
    </footer>
  );
}
