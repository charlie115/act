import Link from "next/link";

import { formatDate, stripHtml } from "../lib/api";

function Item({ item, type }) {
  const subtitle = item.subtitle || stripHtml(item.content).slice(0, 120);

  return (
    <article className="content-list__item">
      <div className="content-list__meta">
        <span>{type}</span>
        <span>{formatDate(item.datetime)}</span>
      </div>
      <h3>{item.title || item.username || item.name}</h3>
      <p>{subtitle}</p>
      {item.url ? (
        <a href={item.url} target="_blank" rel="noreferrer">
          원문 보기
        </a>
      ) : null}
    </article>
  );
}

export default function NewsDigest({ news = [], announcements = [], socialPosts = [] }) {
  return (
    <section className="three-column-grid">
      <div className="surface-card">
        <div className="section-heading">
          <div>
            <p className="eyebrow">News</p>
            <h2>최신 기사</h2>
          </div>
          <Link href="/news">전체 보기</Link>
        </div>
        <div className="content-list">
          {news.map((item) => (
            <Item key={`news-${item.id}`} item={item} type={item.media || "News"} />
          ))}
        </div>
      </div>
      <div className="surface-card">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Announcements</p>
            <h2>거래소 공지</h2>
          </div>
          <Link href="/news">전체 보기</Link>
        </div>
        <div className="content-list">
          {announcements.map((item) => (
            <Item
              key={`announcement-${item.id}`}
              item={item}
              type={item.exchange || item.category || "Announcement"}
            />
          ))}
        </div>
      </div>
      <div className="surface-card">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Social</p>
            <h2>커뮤니티 소셜 피드</h2>
          </div>
          <Link href="/news">전체 보기</Link>
        </div>
        <div className="content-list">
          {socialPosts.map((item) => (
            <Item
              key={`social-${item.id}`}
              item={{ ...item, title: item.username || item.name }}
              type={item.social_media || "Social"}
            />
          ))}
        </div>
      </div>
    </section>
  );
}
