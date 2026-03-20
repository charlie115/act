const siteName = "ArbiCrypto";
const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000";
const defaultDescription =
  "실시간 김프(김치프리미엄) 시세, 거래소 간 프리미엄 차트, 펀딩비 비교, 암호화폐 차익거래에 필요한 모든 데이터를 제공합니다.";

export const siteConfig = {
  siteName,
  siteUrl,
  defaultDescription,
  titleTemplate: `%s | ${siteName}`,
  socials: {
    x: "https://x.com/arbicrypto",
  },
};

export function absoluteUrl(pathname = "/") {
  return new URL(pathname, siteUrl).toString();
}

export function buildMetadata({
  title,
  description = defaultDescription,
  pathname = "/",
  type = "website",
}) {
  const resolvedTitle = title ? `${title} | ${siteName}` : `${siteName} - ACW Next`;
  const url = absoluteUrl(pathname);

  return {
    title: resolvedTitle,
    description,
    alternates: {
      canonical: url,
    },
    openGraph: {
      type,
      title: resolvedTitle,
      description,
      url,
      siteName,
      locale: "ko_KR",
      images: [{ url: absoluteUrl("/images/og-default.png"), width: 1200, height: 630, alt: siteName }],
    },
    twitter: {
      card: "summary_large_image",
      title: resolvedTitle,
      description,
      site: "@arbicrypto",
    },
  };
}
