const routes = [
  "/",
  "/news",
  "/community-board",
  "/arbitrage",
  "/bot",
];

export default function sitemap() {
  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000";

  return routes.map((path) => ({
    url: `${siteUrl}${path}`,
    lastModified: new Date(),
  }));
}
