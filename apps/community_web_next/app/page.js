import BoardPreview from "../components/BoardPreview";
import HomeMarketOverviewClient from "../components/home/HomeMarketOverviewClient";
import NewsDigest from "../components/NewsDigest";
import { getAnnouncements, getBoardPosts, getNews, getSocialPosts } from "../lib/api";
import { buildMetadata } from "../lib/site";

export const metadata = buildMetadata({
  title: "실시간 김프 | 김치프리미엄 차익거래",
  description:
    "실시간 김프(김치프리미엄) 시세, 업비트-바이낸스 프리미엄 차트, 펀딩비 비교까지. 암호화폐 차익거래에 필요한 모든 데이터.",
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
      <header>
        <h1 className="text-2xl font-bold mb-4">실시간 김프(김치프리미엄) 시세</h1>
        <p className="text-ink-muted text-sm mb-6">
          업비트, 바이낸스 등 주요 거래소 간 실시간 프리미엄(김프)을 비교하고, 펀딩비와 차익거래 기회를 분석하세요.
        </p>
      </header>
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
