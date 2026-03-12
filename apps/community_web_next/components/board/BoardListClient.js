"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

import { useAuth } from "../auth/AuthProvider";
import { formatDate, stripHtml } from "../../lib/api";
import { POST_CATEGORY_LIST } from "../../lib/board";

export default function BoardListClient({ count, currentCategory = "", currentPage = 1, posts }) {
  const { loggedIn } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  const searchParams = useSearchParams();
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState(currentCategory);

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

    if (category) {
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
    <section className="surface-card">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Community Board</p>
          <h1>공지와 커뮤니티 대화</h1>
        </div>
        <div className="tab-strip">
          <span className="auth-chip">{count} posts</span>
          {loggedIn ? (
            <Link className="primary-button" href="/community-board/post/new">
              New Post
            </Link>
          ) : null}
        </div>
      </div>

      <div className="news-filter-bar">
        <input
          className="auth-form__input"
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search posts"
          value={query}
        />
        <select
          className="select-input"
          onChange={(event) => {
            const nextCategory = event.target.value;
            setCategory(nextCategory);
            updateQueryParams({ category: nextCategory, page: "1" });
          }}
          value={category}
        >
          <option value="">All Categories</option>
          {POST_CATEGORY_LIST.map((item) => (
            <option key={item.value} value={item.value}>
              {item.value}
            </option>
          ))}
        </select>
      </div>

      {filteredPosts.length ? (
        <div className="board-grid">
          {filteredPosts.map((post) => {
            const categoryItem = POST_CATEGORY_LIST.find((item) => item.value === post.category);

            return (
              <Link
                key={post.id}
                className="board-grid__item"
                href={`/community-board/post/${post.id}`}
              >
                <div className="board-grid__meta">
                  <span style={{ color: categoryItem?.color || undefined }}>
                    {categoryItem?.getLabel?.() || post.category}
                  </span>
                  <span>{post.author_profile?.username || "Unknown"}</span>
                  <span>{formatDate(post.date_created)}</span>
                </div>
                <h3>{post.title}</h3>
                <p>{stripHtml(post.content).slice(0, 180)}</p>
                <div className="board-grid__stats">
                  <span>{post.comments} comments</span>
                  <span>{post.views} views</span>
                  <span>{post.likes} likes</span>
                  <span>{post.dislikes} dislikes</span>
                </div>
              </Link>
            );
          })}
        </div>
      ) : (
        <div className="empty-state">표시할 게시글이 없습니다.</div>
      )}

      {totalPages > 1 ? (
        <div className="pagination-row">
          <button
            className="ghost-button ghost-button--button"
            disabled={currentPage <= 1}
            onClick={() => updateQueryParams({ category, page: String(currentPage - 1) })}
            type="button"
          >
            Previous
          </button>
          <span className="auth-chip">
            Page {currentPage} / {totalPages}
          </span>
          <button
            className="ghost-button ghost-button--button"
            disabled={currentPage >= totalPages}
            onClick={() => updateQueryParams({ category, page: String(currentPage + 1) })}
            type="button"
          >
            Next
          </button>
        </div>
      ) : null}
    </section>
  );
}
