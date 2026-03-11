const siteName = "ArbiCrypto";
const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000";
const defaultDescription =
  "실시간 암호화폐 차익거래 인사이트, 뉴스, 커뮤니티 업데이트를 더 빠르게 확인할 수 있는 ACW 차세대 웹 경험입니다.";

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
    },
    twitter: {
      card: "summary_large_image",
      title: resolvedTitle,
      description,
    },
  };
}
