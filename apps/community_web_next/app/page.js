import BoardPreview from "../components/BoardPreview";
import HeroSection from "../components/HeroSection";
import NewsDigest from "../components/NewsDigest";
import { getAnnouncements, getBoardPosts, getNews, getSocialPosts } from "../lib/api";
import { buildMetadata } from "../lib/site";

export const dynamic = "force-dynamic";

export const metadata = buildMetadata({
  title: "Home",
  description:
    "ArbiCrypto 차세대 공개 프론트. 실시간 뉴스와 커뮤니티 업데이트를 더 빠르게 노출하도록 Next.js로 전환 중입니다.",
  pathname: "/",
});

export default async function HomePage() {
  const [news, announcements, socialPosts, board] = await Promise.all([
    getNews({ page_size: 4 }).catch(() => []),
    getAnnouncements({ page_size: 4 }).catch(() => []),
    getSocialPosts({ page_size: 4 }).catch(() => []),
    getBoardPosts({ page_size: 4 }).catch(() => ({ results: [] })),
  ]);

  return (
    <div className="section-stack">
      <HeroSection />
      <NewsDigest
        news={news}
        announcements={announcements}
        socialPosts={socialPosts}
      />
      <BoardPreview posts={board.results} />
    </div>
  );
}
