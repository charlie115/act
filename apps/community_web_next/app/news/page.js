import { buildMetadata } from "../../lib/site";
import { getNews, getAnnouncements, getSocialPosts } from "../../lib/api";
import NewsHubClient from "../../components/news/NewsHubClient";

export const metadata = buildMetadata({
  title: "암호화폐 뉴스 | 거래소 공지 실시간",
  description: "비트코인, 이더리움 등 암호화폐 실시간 뉴스와 거래소 공지를 한 곳에서 확인하세요.",
  pathname: "/news",
});

async function safeFetch(fetcher, fallback) {
  try {
    return await fetcher();
  } catch {
    return fallback;
  }
}

export default async function NewsPage() {
  const [news, announcements, social] = await Promise.all([
    safeFetch(() => getNews({ page_size: 20 }), []),
    safeFetch(() => getAnnouncements({ page_size: 20 }), []),
    safeFetch(() => getSocialPosts({ page_size: 20 }), []),
  ]);

  return (
    <NewsHubClient
      initialData={{ news, announcements, social }}
    />
  );
}
