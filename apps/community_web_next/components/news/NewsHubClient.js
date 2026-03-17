"use client";

import { useEffect, useMemo, useState } from "react";
import { CalendarDays, Search } from "lucide-react";

import { formatDate, stripHtml } from "../../lib/api";
import { fetchCachedJson } from "../../lib/clientCache";
import SurfaceNotice from "../ui/SurfaceNotice";

const TABS = [
  { key: "news", label: "전체 뉴스" },
  { key: "social", label: "소셜" },
  { key: "announcements", label: "거래소 공지" },
];

const ANNOUNCEMENT_CATEGORIES = [
  "Notice",
  "Maintenance",
  "New Listing",
  "Delisting",
  "Deposit/Withdrawal",
  "Airdrop",
];

const CATEGORY_LABELS = {
  Notice: "공지",
  Maintenance: "점검",
  "New Listing": "신규 상장",
  Delisting: "상장 폐지",
  "Deposit/Withdrawal": "입출금",
  Airdrop: "에어드롭",
};

function toApiDateRange(value, edge) {
  if (!value) {
    return undefined;
  }

  return edge === "start"
    ? `${value}T00:00:00`
    : `${value}T23:59:59`;
}

function NewsCard({ item, secondary }) {
  return (
    <article className="rounded-lg border border-border bg-background/70 p-4 transition-colors hover:bg-surface-elevated/30">
      <div className="mb-1.5 flex items-center gap-2 text-[0.68rem] text-ink-muted">
        <span className="rounded bg-accent/10 px-1.5 py-0.5 font-bold text-accent">{secondary}</span>
        <span>{formatDate(item.datetime)}</span>
      </div>
      <h2 className="text-sm font-semibold text-ink">{item.title || item.username || item.name}</h2>
      <p className="mt-1 text-[0.78rem] leading-relaxed text-ink-muted">
        {item.subtitle || stripHtml(item.content).slice(0, 220)}
      </p>
      {item.url ? (
        <div className="mt-2">
          <a
            className="text-xs font-semibold text-accent hover:text-accent/80"
            href={item.url}
            rel="noreferrer"
            target="_blank"
          >
            원문 열기
          </a>
        </div>
      ) : null}
    </article>
  );
}

export default function NewsHubClient() {
  const [activeTab, setActiveTab] = useState("news");
  const [query, setQuery] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [announcementCategories, setAnnouncementCategories] = useState([]);
  const [pageError, setPageError] = useState("");
  const [news, setNews] = useState([]);
  const [social, setSocial] = useState([]);
  const [announcements, setAnnouncements] = useState([]);
  const [loadedTabs, setLoadedTabs] = useState({
    news: false,
    social: false,
    announcements: false,
  });

  useEffect(() => {
    let active = true;

    async function loadData() {
      setPageError("");

      const searchParams = new URLSearchParams();
      const startTime = toApiDateRange(startDate, "start");
      const endTime = toApiDateRange(endDate, "end");

      if (startTime) searchParams.set("start_time", startTime);
      if (endTime) searchParams.set("end_time", endTime);
      searchParams.set("tz", "Asia/Seoul");

      const suffix = searchParams.toString() ? `?${searchParams.toString()}` : "";

      try {
        if (activeTab === "news") {
          const newsResponse = await fetchCachedJson(`/api/newscore/news/${suffix}`, {
            ttlMs: 60000,
          });
          if (!active) return;
          setNews(newsResponse?.results || []);
          setLoadedTabs((current) => ({ ...current, news: true }));
        }

        if (activeTab === "social") {
          const socialResponse = await fetchCachedJson(`/api/newscore/posts/${suffix}`, {
            ttlMs: 60000,
          });
          if (!active) return;
          setSocial(socialResponse?.results || []);
          setLoadedTabs((current) => ({ ...current, social: true }));
        }

        if (activeTab === "announcements") {
          const announcementResponse = await fetchCachedJson(
            `/api/newscore/announcements/${suffix}`,
            { ttlMs: 60000 }
          );
          if (!active) return;
          setAnnouncements(announcementResponse?.results || []);
          setLoadedTabs((current) => ({ ...current, announcements: true }));
        }
      } catch (requestError) {
        if (!active) {
          return;
        }

        setPageError(requestError.message || "뉴스를 불러오지 못했습니다.");
      }
    }

    loadData();

    return () => {
      active = false;
    };
  }, [activeTab, endDate, startDate]);

  const normalizedQuery = query.trim().toLowerCase();

  const filteredNews = useMemo(() => {
    if (!normalizedQuery) {
      return news;
    }

    return news.filter((item) =>
      `${item.title} ${item.subtitle || ""} ${item.content || ""}`
        .toLowerCase()
        .includes(normalizedQuery)
    );
  }, [news, normalizedQuery]);

  const filteredSocial = useMemo(() => {
    if (!normalizedQuery) {
      return social;
    }

    return social.filter((item) =>
      `${item.username || ""} ${item.name || ""} ${item.content || ""}`
        .toLowerCase()
        .includes(normalizedQuery)
    );
  }, [normalizedQuery, social]);

  const filteredAnnouncements = useMemo(() => {
    let items = announcements;

    if (announcementCategories.length) {
      items = items.filter((item) => announcementCategories.includes(item.category));
    }

    if (!normalizedQuery) {
      return items;
    }

    return items.filter((item) =>
      `${item.title} ${item.content || ""} ${item.exchange || ""}`
        .toLowerCase()
        .includes(normalizedQuery)
    );
  }, [announcementCategories, announcements, normalizedQuery]);

  const currentItems =
    activeTab === "news"
      ? filteredNews
      : activeTab === "social"
        ? filteredSocial
        : filteredAnnouncements;

  return (
    <div className="grid gap-4">
      {/* Header + tabs */}
      <div className="flex flex-wrap items-end justify-between gap-3">
        <h1 className="text-lg font-bold text-ink">시장 뉴스</h1>
        <div className="flex flex-wrap gap-1">
          {TABS.map((tab) => (
            <button
              key={tab.key}
              className={`rounded-lg px-3 py-1.5 text-xs font-bold transition-colors ${
                activeTab === tab.key
                  ? "bg-accent/15 text-accent"
                  : "text-ink-muted hover:bg-surface-elevated/40 hover:text-ink"
              }`}
              onClick={() => setActiveTab(tab.key)}
              type="button"
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-end gap-2">
        <div className="relative flex-1 min-w-[160px]">
          <Search className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 text-ink-muted" size={14} strokeWidth={2} />
          <input
            className="w-full rounded-lg border border-border bg-background/70 py-1.5 pl-8 pr-3 text-sm text-ink placeholder:text-ink-muted/60 outline-none transition-colors focus:border-accent/40"
            onChange={(event) => setQuery(event.target.value)}
            placeholder="뉴스 검색"
            value={query}
          />
        </div>
        <label className="flex flex-col gap-1">
          <span className="text-[0.62rem] font-bold uppercase tracking-wider text-ink-muted">시작</span>
          <span className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-background/70 px-2.5 py-1.5">
            <CalendarDays className="text-ink-muted" size={14} strokeWidth={2} />
            <input
              className="bg-transparent text-sm text-ink outline-none"
              onChange={(event) => setStartDate(event.target.value)}
              type="date"
              value={startDate}
            />
          </span>
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-[0.62rem] font-bold uppercase tracking-wider text-ink-muted">종료</span>
          <span className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-background/70 px-2.5 py-1.5">
            <CalendarDays className="text-ink-muted" size={14} strokeWidth={2} />
            <input
              className="bg-transparent text-sm text-ink outline-none"
              onChange={(event) => setEndDate(event.target.value)}
              type="date"
              value={endDate}
            />
          </span>
        </label>
      </div>

      {/* Announcement category filter */}
      {activeTab === "announcements" ? (
        <div className="flex flex-wrap gap-1.5">
          {ANNOUNCEMENT_CATEGORIES.map((category) => {
            const selected = announcementCategories.includes(category);
            return (
              <button
                key={category}
                className={`rounded-md px-2.5 py-2 text-xs font-bold transition-colors ${
                  selected
                    ? "bg-accent/15 text-accent"
                    : "text-ink-muted hover:bg-surface-elevated/40 hover:text-ink"
                }`}
                onClick={() =>
                  setAnnouncementCategories((current) =>
                    selected
                      ? current.filter((item) => item !== category)
                      : current.concat(category)
                  )
                }
                type="button"
              >
                {CATEGORY_LABELS[category] || category}
              </button>
            );
          })}
        </div>
      ) : null}

      {/* Results */}
      <div className="grid gap-2">
        {currentItems.length ? (
          currentItems.map((item) => (
            <NewsCard
              key={`${activeTab}-${item.id}`}
              item={item}
              secondary={
                activeTab === "news"
                  ? item.media || "뉴스"
                  : activeTab === "social"
                    ? item.social_media || "소셜"
                    : item.exchange || (CATEGORY_LABELS[item.category] || item.category) || "공지"
              }
            />
          ))
        ) : (
          <div className="grid min-h-[120px] place-items-center rounded-lg bg-surface-elevated/20 text-sm text-ink-muted">
            표시할 항목이 없습니다.
          </div>
        )}
      </div>
      {pageError ? <SurfaceNotice description={pageError} variant="error" /> : null}
    </div>
  );
}
