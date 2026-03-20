const staticRoutes = [
  { path: "/", changeFrequency: "hourly", priority: 1.0 },
  { path: "/news", changeFrequency: "hourly", priority: 0.9 },
  { path: "/arbitrage", changeFrequency: "hourly", priority: 0.8 },
  {
    path: "/arbitrage/funding-rate/diff",
    changeFrequency: "hourly",
    priority: 0.7,
  },
  {
    path: "/arbitrage/funding-rate/avg",
    changeFrequency: "hourly",
    priority: 0.7,
  },
  { path: "/community-board", changeFrequency: "daily", priority: 0.6 },
];

export default async function sitemap() {
  const siteUrl =
    process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000";

  const staticEntries = staticRoutes.map(
    ({ path, changeFrequency, priority }) => ({
      url: `${siteUrl}${path}`,
      lastModified: new Date(),
      changeFrequency,
      priority,
    }),
  );

  let postEntries = [];
  try {
    const apiBase =
      process.env.ACW_API_PROXY_TARGET?.replace(/\/$/, "") ||
      process.env.NEXT_PUBLIC_DRF_URL?.replace(/\/$/, "") ||
      "http://localhost:8000";

    const res = await fetch(`${apiBase}/board/posts/?page_size=100`, {
      next: { revalidate: 3600 },
      headers: { Accept: "application/json" },
    });

    if (res.ok) {
      const data = await res.json();
      const posts = data?.results || [];

      postEntries = posts.map((post) => ({
        url: `${siteUrl}/community-board/post/${post.id}`,
        lastModified: post.updated_at
          ? new Date(post.updated_at)
          : new Date(),
        changeFrequency: "weekly",
        priority: 0.4,
      }));
    }
  } catch {
    // Silently skip dynamic entries if the API is unreachable
  }

  return [...staticEntries, ...postEntries];
}
