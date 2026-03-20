export default function robots() {
  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000";

  return {
    rules: {
      userAgent: "*",
      allow: "/",
      disallow: [
        "/bot/",
        "/my-page",
        "/coupon-dashboard",
        "/affiliate/",
        "/request-affiliate",
        "/login",
        "/register",
        "/api/",
      ],
    },
    sitemap: `${siteUrl}/sitemap.xml`,
  };
}
