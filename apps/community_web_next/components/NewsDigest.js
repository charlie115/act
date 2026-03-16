import Link from "next/link";
import { BellRing, MessageSquareQuote, Newspaper } from "lucide-react";

import { formatDate, stripHtml } from "../lib/api";

function Item({ item, type }) {
  const subtitle = item.subtitle || stripHtml(item.content).slice(0, 120);

  return (
    <article className="border-b border-border/50 py-3 last:border-b-0 last:pb-0 first:pt-1 transition-colors hover:bg-surface-elevated/20 -mx-2 px-2 rounded-lg">
      <div className="mb-1 flex flex-wrap gap-2 text-[0.68rem] text-ink-muted">
        <span>{type}</span>
        <span>{formatDate(item.datetime)}</span>
      </div>
      <h3 className="mb-1.5 text-base font-bold text-ink">{item.title || item.username || item.name}</h3>
      <p className="text-sm leading-relaxed text-ink-muted">{subtitle}</p>
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

function ColumnCard({ eyebrow, title, badgeIcon: BadgeIcon, badgeText, items, renderItem }) {
  return (
    <div className="rounded-xl border border-border bg-background/92 p-5 transition-shadow hover:shadow-lg">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <p className="mb-1.5 text-[0.66rem] font-bold uppercase tracking-[0.14em] text-accent">{eyebrow}</p>
          <h2 className="text-lg font-bold text-ink">{title}</h2>
        </div>
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1.5 rounded-full border border-border bg-background/70 px-3 py-1 text-[0.78rem] font-bold text-ink-muted">
            <BadgeIcon size={14} strokeWidth={2} />
            {badgeText}
          </span>
          <Link
            className="inline-flex items-center rounded-lg border border-border/50 bg-background/70 px-3 py-1.5 text-xs font-bold text-ink-muted transition-colors hover:border-accent/30 hover:text-ink"
            href="/news"
          >
            전체 보기
          </Link>
        </div>
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
        eyebrow="News"
        title="최신 기사"
        badgeIcon={Newspaper}
        badgeText="Media"
        items={news}
        renderItem={(item) => (
          <Item key={`news-${item.id}`} item={item} type={item.media || "News"} />
        )}
      />
      <ColumnCard
        eyebrow="Announcements"
        title="거래소 공지"
        badgeIcon={BellRing}
        badgeText="Notices"
        items={announcements}
        renderItem={(item) => (
          <Item
            key={`announcement-${item.id}`}
            item={item}
            type={item.exchange || item.category || "Announcement"}
          />
        )}
      />
      <ColumnCard
        eyebrow="Social"
        title="커뮤니티 소셜 피드"
        badgeIcon={MessageSquareQuote}
        badgeText="Social"
        items={socialPosts}
        renderItem={(item) => (
          <Item
            key={`social-${item.id}`}
            item={{ ...item, title: item.username || item.name }}
            type={item.social_media || "Social"}
          />
        )}
      />
    </section>
  );
}
