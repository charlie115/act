"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { Search } from "lucide-react";

import { useAuth } from "../auth/AuthProvider";
import { formatDate, stripHtml } from "../../lib/api";
import { POST_CATEGORY_LIST } from "../../lib/board";

const CATEGORY_COLORS = POST_CATEGORY_LIST.reduce((acc, cat) => {
  acc[cat.value] = cat.color;
  return acc;
}, {});

export default function BoardListClient({ count, currentCategory = "", currentPage = 1, posts }) {
  const { loggedIn } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  const searchParams = useSearchParams();
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState(currentCategory || "all");

  const totalPages = useMemo(() => {
    const pageSize = posts.length || 20;
    return pageSize ? Math.max(1, Math.ceil(count / pageSize)) : 1;
  }, [count, posts.length]);

  function updateQueryParams(nextValues) {
    const params = new URLSearchParams(searchParams?.toString() || "");

    Object.entries(nextValues).forEach(([key, value]) => {
      if (!value || value === "1") {
        params.delete(key);
      } else {
        params.set(key, value);
      }
    });

    const queryString = params.toString();
    router.push(queryString ? `${pathname}?${queryString}` : pathname);
  }

  const filteredPosts = useMemo(() => {
    let items = posts;

    if (category && category !== "all") {
      items = items.filter((post) => post.category === category);
    }

    const normalizedQuery = query.trim().toLowerCase();
    if (!normalizedQuery) {
      return items;
    }

    return items.filter((post) =>
      `${post.title} ${post.content || ""}`.toLowerCase().includes(normalizedQuery)
    );
  }, [category, posts, query]);

  return (
    <div className="grid gap-4">
      {/* Header */}
      <div className="flex flex-wrap items-end justify-between gap-3">
        <h1 className="text-lg font-bold text-ink">게시판</h1>
        <div className="flex items-center gap-2">
          <span className="rounded bg-accent/10 px-2 py-0.5 text-[0.66rem] font-bold tabular-nums text-accent">
            {count}개 게시글
          </span>
          {loggedIn ? (
            <Link
              className="rounded-lg bg-accent px-3 py-1.5 text-xs font-bold text-white transition-colors hover:bg-accent/90"
              href="/community-board/post/new"
            >
              새 글 작성
            </Link>
          ) : null}
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-end gap-2">
        <div className="relative flex-1 min-w-[160px]">
          <Search className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 text-ink-muted" size={14} strokeWidth={2} />
          <input
            className="w-full rounded-lg border border-border bg-background/70 py-1.5 pl-8 pr-3 text-sm text-ink placeholder:text-ink-muted/60 outline-none transition-colors focus:border-accent/40"
            onChange={(event) => setQuery(event.target.value)}
            placeholder="게시글 검색"
            value={query}
          />
        </div>
        <div className="flex gap-1">
          <button
            className={`rounded-md px-2.5 py-1.5 text-xs font-bold transition-colors ${
              category === "all"
                ? "bg-accent/15 text-accent"
                : "text-ink-muted hover:bg-surface-elevated/40 hover:text-ink"
            }`}
            onClick={() => {
              setCategory("all");
              updateQueryParams({ category: "", page: "1" });
            }}
            type="button"
          >
            전체
          </button>
          {POST_CATEGORY_LIST.map((item) => (
            <button
              key={item.value}
              className={`rounded-md px-2.5 py-1.5 text-xs font-bold transition-colors ${
                category === item.value
                  ? "bg-accent/15 text-accent"
                  : "text-ink-muted hover:bg-surface-elevated/40 hover:text-ink"
              }`}
              onClick={() => {
                setCategory(item.value);
                updateQueryParams({ category: item.value, page: "1" });
              }}
              type="button"
            >
              {item.getLabel?.() || item.value}
            </button>
          ))}
        </div>
      </div>

      {/* Post list */}
      {filteredPosts.length ? (
        <div className="grid gap-2">
          {filteredPosts.map((post) => {
            const catColor = CATEGORY_COLORS[post.category] || "#8f9bb7";
            const categoryItem = POST_CATEGORY_LIST.find((item) => item.value === post.category);

            return (
              <Link
                key={post.id}
                className="group grid gap-2 rounded-lg border border-border bg-background/70 p-3.5 transition-all hover:-translate-y-px hover:border-accent/20 hover:bg-surface-elevated/40"
                href={`/community-board/post/${post.id}`}
              >
                <div className="flex flex-wrap items-center gap-2 text-[0.68rem] text-ink-muted">
                  <span
                    className="rounded px-1.5 py-0.5 text-[0.64rem] font-bold"
                    style={{ backgroundColor: `${catColor}22`, color: catColor }}
                  >
                    {categoryItem?.getLabel?.() || post.category}
                  </span>
                  <span>{post.author_profile?.username || "익명"}</span>
                  <span>{formatDate(post.date_created)}</span>
                </div>
                <div className="grid gap-3 sm:grid-cols-[1fr_auto] sm:items-center">
                  <div>
                    <h3 className="mb-1 text-sm font-bold text-ink group-hover:text-accent transition-colors">{post.title}</h3>
                    <p className="text-[0.82rem] leading-relaxed text-ink-muted">{stripHtml(post.content).slice(0, 180)}</p>
                  </div>
                  <div className="flex flex-wrap gap-2 font-mono text-[0.68rem] text-ink-muted sm:flex-col sm:items-end">
                    <span>{post.comments} 댓글</span>
                    <span>{post.views} 조회</span>
                    <span>{post.likes} 좋아요</span>
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      ) : (
        <div className="grid min-h-[120px] place-items-center rounded-lg bg-surface-elevated/20 text-sm text-ink-muted">
          표시할 게시글이 없습니다.
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 ? (
        <div className="flex items-center justify-center gap-3">
          <button
            className="rounded-lg border border-border px-3 py-1.5 text-xs font-bold text-ink-muted transition-colors hover:bg-surface-elevated/40 hover:text-ink disabled:opacity-30 disabled:cursor-not-allowed"
            disabled={currentPage <= 1}
            onClick={() => updateQueryParams({ category, page: String(currentPage - 1) })}
            type="button"
          >
            이전
          </button>
          <span className="text-xs tabular-nums text-ink-muted">
            {currentPage} / {totalPages}
          </span>
          <button
            className="rounded-lg border border-border px-3 py-1.5 text-xs font-bold text-ink-muted transition-colors hover:bg-surface-elevated/40 hover:text-ink disabled:opacity-30 disabled:cursor-not-allowed"
            disabled={currentPage >= totalPages}
            onClick={() => updateQueryParams({ category, page: String(currentPage + 1) })}
            type="button"
          >
            다음
          </button>
        </div>
      ) : null}
    </div>
  );
}
