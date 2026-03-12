"use client";

import { useEffect, useMemo, useState } from "react";

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
    <article className="stacked-list__item">
      <div className="content-list__meta">
        <span>{secondary}</span>
        <span>{formatDate(item.datetime)}</span>
      </div>
      <h2>{item.title || item.username || item.name}</h2>
      <p>{item.subtitle || stripHtml(item.content).slice(0, 220)}</p>
      {item.url ? (
        <a href={item.url} rel="noreferrer" target="_blank">
          원문 열기
        </a>
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

        setPageError(requestError.message || "뉴스 허브를 불러오지 못했습니다.");
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
    <div className="section-stack">
      <section className="surface-card">
        <div className="section-heading">
          <div>
            <p className="eyebrow">News Hub</p>
            <h1>시장 뉴스, 공지, 소셜 피드</h1>
          </div>
          <div className="tab-strip">
            {TABS.map((tab) => (
              <button
                key={tab.key}
                className={`tab-pill ghost-button--button${activeTab === tab.key ? " tab-pill--active" : ""}`}
                onClick={() => setActiveTab(tab.key)}
                type="button"
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        <div className="news-filter-bar">
          <input
            className="auth-form__input"
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search news"
            value={query}
          />
          <input
            className="auth-form__input"
            onChange={(event) => setStartDate(event.target.value)}
            type="date"
            value={startDate}
          />
          <input
            className="auth-form__input"
            onChange={(event) => setEndDate(event.target.value)}
            type="date"
            value={endDate}
          />
        </div>

        {activeTab === "announcements" ? (
          <div className="tab-strip">
            {ANNOUNCEMENT_CATEGORIES.map((category) => {
              const selected = announcementCategories.includes(category);
              return (
                <button
                  key={category}
                  className={`tab-pill ghost-button--button${selected ? " tab-pill--active" : ""}`}
                  onClick={() =>
                    setAnnouncementCategories((current) =>
                      selected
                        ? current.filter((item) => item !== category)
                        : current.concat(category)
                    )
                  }
                  type="button"
                >
                  {category}
                </button>
              );
            })}
          </div>
        ) : null}
      </section>

      <section className="surface-card">
        <div className="stacked-list">
          {currentItems.length ? (
            currentItems.map((item) => (
              <NewsCard
                key={`${activeTab}-${item.id}`}
                item={item}
                secondary={
                  activeTab === "news"
                    ? item.media || "News"
                    : activeTab === "social"
                      ? item.social_media || "Social"
                      : item.exchange || item.category || "Announcement"
                }
              />
            ))
          ) : (
            <div className="empty-state">표시할 항목이 없습니다.</div>
          )}
        </div>
        {pageError ? <SurfaceNotice description={pageError} variant="error" /> : null}
      </section>
    </div>
  );
}
