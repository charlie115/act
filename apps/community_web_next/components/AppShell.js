"use client";

import Link from "next/link";
import { useMemo } from "react";
import { usePathname } from "next/navigation";

import AuthActions from "./auth/AuthActions";
import NextBreadcrumbs from "./NextBreadcrumbs";

const routeMeta = [
  { match: "/", label: "Home" },
  { match: "/news", label: "News" },
  { match: "/community-board", label: "Board" },
  { match: "/arbitrage", label: "Arbitrage" },
  { match: "/bot", label: "Bot" },
  { match: "/coupon-dashboard", label: "Coupons" },
  { match: "/request-affiliate", label: "Affiliate" },
  { match: "/affiliate", label: "Affiliate" },
  { match: "/my-page", label: "My Page" },
];

export default function AppShell({ children }) {
  const pathname = usePathname();

  const currentMeta = useMemo(() => {
    const matched = routeMeta.find((item) =>
      item.match === "/" ? pathname === "/" : pathname.startsWith(item.match)
    );

    return matched || { label: "ACW" };
  }, [pathname]);

  return (
    <div className="site-shell">
      <header className="site-header">
        <div className="site-header__inner">
          <Link className="site-brand" href="/">
            <span className="site-brand__mark">ACW</span>
            <span className="site-brand__text">
              <strong>ArbiCrypto</strong>
              <small>{currentMeta.label}</small>
            </span>
          </Link>

          <nav className="site-nav" aria-label="Primary">
            {routeMeta.map((item) => {
              const active =
                item.match === "/"
                  ? pathname === "/"
                  : pathname.startsWith(item.match);

              return (
                <Link
                  key={item.match}
                  className={`site-nav__link${active ? " site-nav__link--active" : ""}`}
                  href={item.match}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>

          <div className="site-header__actions">
            <AuthActions />
          </div>
        </div>
      </header>
      <div className="page-frame">
        <NextBreadcrumbs />
      </div>
      <main className="page-frame">{children}</main>
    </div>
  );
}
