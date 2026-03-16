import BoardPreview from "../components/BoardPreview";
import HomeMarketOverviewClient from "../components/home/HomeMarketOverviewClient";
import NewsDigest from "../components/NewsDigest";
import { getAnnouncements, getBoardPosts, getNews, getSocialPosts } from "../lib/api";
import { buildMetadata } from "../lib/site";

export const metadata = buildMetadata({
  title: "Home",
  description:
    "ArbiCrypto 홈 화면. 실시간 프리미엄 데이터와 시장 조합 탐색을 Next.js 환경에서 제공합니다.",
  pathname: "/",
});

async function safeFetch(fetcher, fallback) {
  try {
    return await fetcher();
  } catch {
    return fallback;
  }
}

export default async function HomePage() {
  const [news, announcements, socialPosts, boardData] = await Promise.all([
    safeFetch(() => getNews({ page_size: 4 }), []),
    safeFetch(() => getAnnouncements({ page_size: 4 }), []),
    safeFetch(() => getSocialPosts({ page_size: 4 }), []),
    safeFetch(() => getBoardPosts({ page_size: 4 }), { count: 0, results: [] }),
  ]);

  return (
    <div className="grid gap-6">
      <HomeMarketOverviewClient />
      <NewsDigest
        announcements={announcements.slice(0, 3)}
        news={news.slice(0, 3)}
        socialPosts={socialPosts.slice(0, 3)}
      />
      <BoardPreview posts={boardData.results.slice(0, 4)} />
    </div>
  );
}
