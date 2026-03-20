"use client";

import Link from "next/link";
import { useMemo } from "react";
import { usePathname } from "next/navigation";

import { siteConfig } from "../lib/site";

const LABELS = {
  affiliate: "제휴",
  arbitrage: "아비트리지",
  board: "게시판",
  bot: "봇",
  capital: "자본",
  "commission-history": "수수료 내역",
  "community-board": "게시판",
  "coupon-dashboard": "쿠폰",
  dashboard: "대시보드",
  deposit: "입금",
  diff: "차이",
  "funding-rate": "펀딩비",
  login: "로그인",
  "my-page": "마이페이지",
  news: "뉴스",
  "pnl-history": "손익 내역",
  position: "포지션",
  post: "게시글",
  register: "회원가입",
  "request-affiliate": "제휴 신청",
  scanner: "스캐너",
  settings: "설정",
  triggers: "트리거",
  avg: "평균",
  new: "새 글",
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
      label: /^\d+$/.test(segment) ? "상세" : prettifySegment(segment),
    }));
  }, [pathname]);

  const breadcrumbJsonLd = useMemo(() => {
    if (!crumbs.length) return null;

    const items = [
      {
        "@type": "ListItem",
        position: 1,
        name: "홈",
        item: siteConfig.siteUrl,
      },
      ...crumbs.map((crumb, index) => ({
        "@type": "ListItem",
        position: index + 2,
        name: crumb.label,
        item: `${siteConfig.siteUrl}${crumb.href}`,
      })),
    ];

    return {
      "@context": "https://schema.org",
      "@type": "BreadcrumbList",
      itemListElement: items,
    };
  }, [crumbs]);

  if (!crumbs.length) {
    return null;
  }

  return (
    <nav aria-label="Breadcrumb" className="next-breadcrumbs">
      {breadcrumbJsonLd && (
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbJsonLd) }}
        />
      )}
      <Link className="next-breadcrumbs__link" href="/">
        홈
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
