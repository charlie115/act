"use client";

import Link from "next/link";
import { useMemo } from "react";
import { usePathname } from "next/navigation";

const LABELS = {
  affiliate: "Affiliate",
  arbitrage: "Arbitrage",
  board: "Board",
  bot: "Bot",
  capital: "Capital",
  "commission-history": "Commission History",
  "community-board": "Community Board",
  "coupon-dashboard": "Coupon Dashboard",
  dashboard: "Dashboard",
  deposit: "Deposit",
  diff: "Difference",
  "funding-rate": "Funding Rate",
  login: "Login",
  "my-page": "My Page",
  news: "News",
  "pnl-history": "PnL History",
  position: "Position",
  post: "Post",
  register: "Register",
  "request-affiliate": "Affiliate Request",
  scanner: "Scanner",
  settings: "Settings",
  triggers: "Triggers",
};

function prettifySegment(segment) {
  return (
    LABELS[segment] ||
    segment
      .split("-")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ")
  );
}

export default function NextBreadcrumbs() {
  const pathname = usePathname();

  const crumbs = useMemo(() => {
    const segments = pathname.split("/").filter(Boolean);

    return segments.map((segment, index) => ({
      href: `/${segments.slice(0, index + 1).join("/")}`,
      label: /^\d+$/.test(segment) ? "Detail" : prettifySegment(segment),
    }));
  }, [pathname]);

  if (!crumbs.length) {
    return null;
  }

  return (
    <nav aria-label="Breadcrumb" className="next-breadcrumbs">
      <Link className="next-breadcrumbs__link" href="/">
        Home
      </Link>
      {crumbs.map((crumb, index) => {
        const isLast = index === crumbs.length - 1;
        return (
          <span key={crumb.href} className="next-breadcrumbs__item">
            <span className="next-breadcrumbs__separator">/</span>
            {isLast ? (
              <span className="next-breadcrumbs__current">{crumb.label}</span>
            ) : (
              <Link className="next-breadcrumbs__link" href={crumb.href}>
                {crumb.label}
              </Link>
            )}
          </span>
        );
      })}
    </nav>
  );
}
