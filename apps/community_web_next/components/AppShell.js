"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import BrandLogo from "../../community_web/src/components/BrandLogo";
import AuthActions from "./auth/AuthActions";

const navItems = [
  { href: "/", label: "Overview" },
  { href: "/news", label: "News" },
  { href: "/community-board", label: "Board" },
  { href: "/arbitrage", label: "Arbitrage" },
  { href: "/bot", label: "Bot" },
];

export default function AppShell({ children }) {
  const pathname = usePathname();

  return (
    <div className="site-shell">
      <header className="site-header">
        <div className="site-header__inner">
          <Link className="site-brand" href="/" aria-label="ArbiCrypto Home">
            <BrandLogo size={150} />
          </Link>
          <nav className="site-nav" aria-label="Main navigation">
            {navItems.map((item) => (
              <Link
                key={item.href}
                className={`site-nav__link${
                  pathname === item.href || pathname.startsWith(`${item.href}/`)
                    ? " site-nav__link--active"
                    : ""
                }`}
                href={item.href}
              >
                {item.label}
              </Link>
            ))}
          </nav>
          <div className="site-header__actions">
            <AuthActions />
          </div>
        </div>
      </header>
      <main className="page-frame page-frame--legacy">{children}</main>
    </div>
  );
}
