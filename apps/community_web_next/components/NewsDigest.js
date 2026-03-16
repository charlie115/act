import Link from "next/link";

import { formatDate, stripHtml } from "../lib/api";

function Item({ item, type }) {
  const subtitle = item.subtitle || stripHtml(item.content).slice(0, 120);

  return (
    <article className="border-b border-border/50 py-3 last:border-b-0 last:pb-0 first:pt-1 transition-colors hover:bg-surface-elevated/20 -mx-2 px-2 rounded-lg">
      <div className="mb-1 flex flex-wrap gap-2 text-[0.68rem] text-ink-muted">
        <span>{type}</span>
        <span>{formatDate(item.datetime)}</span>
      </div>
      <h3 className="mb-1.5 text-base font-bold text-ink truncate">{item.title || item.username || item.name}</h3>
      <p className="text-sm leading-relaxed text-ink-muted line-clamp-2">{subtitle}</p>
      {item.url ? (
        <a
          href={item.url}
          target="_blank"
          rel="noreferrer"
          className="mt-1.5 inline-block text-sm font-semibold text-accent hover:underline"
        >
          원문 보기
        </a>
      ) : null}
    </article>
  );
}

function ColumnCard({ title, items, renderItem }) {
  return (
    <div className="rounded-xl border border-border bg-background/92 p-5 transition-shadow hover:shadow-lg overflow-hidden">
      <div className="mb-4 flex items-center justify-between gap-3">
        <h2 className="text-sm font-bold text-ink">{title}</h2>
        <Link
          className="text-xs font-semibold text-ink-muted transition-colors hover:text-accent"
          href="/news"
        >
          전체 보기
        </Link>
      </div>
      <div className="grid gap-1">
        {items.map(renderItem)}
      </div>
    </div>
  );
}

export default function NewsDigest({ news = [], announcements = [], socialPosts = [] }) {
  return (
    <section className="grid grid-cols-1 gap-5 lg:grid-cols-3">
      <ColumnCard
        title="최신 기사"
        items={news}
        renderItem={(item) => (
          <Item key={`news-${item.id}`} item={item} type={item.media || "뉴스"} />
        )}
      />
      <ColumnCard
        title="거래소 공지"
        items={announcements}
        renderItem={(item) => (
          <Item
            key={`announcement-${item.id}`}
            item={item}
            type={item.exchange || item.category || "공지"}
          />
        )}
      />
      <ColumnCard
        title="소셜 피드"
        items={socialPosts}
        renderItem={(item) => (
          <Item
            key={`social-${item.id}`}
            item={{ ...item, title: item.username || item.name }}
            type={item.social_media || "소셜"}
          />
        )}
      />
    </section>
  );
}
