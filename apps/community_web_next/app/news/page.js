import { getAnnouncements, getNews, getSocialPosts, stripHtml, formatDate } from "../../lib/api";
import { buildMetadata } from "../../lib/site";

export const dynamic = "force-dynamic";

export const metadata = buildMetadata({
  title: "News",
  description: "뉴스, SNS, 거래소 공지를 서버 렌더링으로 제공하는 ACW Next 뉴스 허브입니다.",
  pathname: "/news",
});

function NewsSection({ title, eyebrow, items, typeResolver }) {
  return (
    <section className="surface-card">
      <div className="section-heading">
        <div>
          <p className="eyebrow">{eyebrow}</p>
          <h1>{title}</h1>
        </div>
      </div>
      <div className="stacked-list">
        {items.length ? (
          items.map((item) => (
            <article key={`${eyebrow}-${item.id}`} className="stacked-list__item">
              <div className="content-list__meta">
                <span>{typeResolver(item)}</span>
                <span>{formatDate(item.datetime)}</span>
              </div>
              <h2>{item.title || item.username || item.name}</h2>
              <p>{item.subtitle || stripHtml(item.content).slice(0, 180)}</p>
              {item.url ? (
                <a href={item.url} target="_blank" rel="noreferrer">
                  원문 열기
                </a>
              ) : null}
            </article>
          ))
        ) : (
          <div className="empty-state">표시할 데이터가 없습니다.</div>
        )}
      </div>
    </section>
  );
}

export default async function NewsPage() {
  const [news, announcements, socialPosts] = await Promise.all([
    getNews().catch(() => []),
    getAnnouncements().catch(() => []),
    getSocialPosts().catch(() => []),
  ]);

  return (
    <div className="news-page-grid">
      <NewsSection
        title="최신 뉴스"
        eyebrow="News"
        items={news}
        typeResolver={(item) => item.media || "News"}
      />
      <NewsSection
        title="거래소 공지"
        eyebrow="Announcements"
        items={announcements}
        typeResolver={(item) => item.exchange || item.category || "Announcement"}
      />
      <NewsSection
        title="소셜 피드"
        eyebrow="Social"
        items={socialPosts}
        typeResolver={(item) => item.social_media || "Social"}
      />
    </div>
  );
}
