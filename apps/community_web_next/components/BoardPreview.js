import Link from "next/link";
import { MessageSquareQuote } from "lucide-react";

import { formatDate, stripHtml } from "../lib/api";
import { POST_CATEGORY_LIST } from "../lib/board";

const CATEGORY_COLORS = POST_CATEGORY_LIST.reduce((acc, cat) => {
  acc[cat.value] = cat.color;
  return acc;
}, {});

export default function BoardPreview({ posts = [] }) {
  return (
    <section className="rounded-lg border border-border bg-background/92 p-4">
      <div className="mb-3 flex items-center justify-between gap-3">
        <h2 className="text-sm font-bold text-ink">최근 게시글</h2>
        <Link
          className="text-xs font-semibold text-ink-muted transition-colors hover:text-accent"
          href="/community-board"
        >
          게시판 이동
        </Link>
      </div>

      {posts.length ? (
        <div className="grid gap-2.5">
          {posts.map((post) => {
            const catColor = CATEGORY_COLORS[post.category] || "#8f9bb7";
            return (
              <Link
                key={post.id}
                className="group grid gap-2 rounded-lg border border-border bg-background/70 p-3.5 transition-all hover:-translate-y-px hover:border-accent/20 hover:bg-surface-elevated/40"
                href={`/community-board/post/${post.id}`}
              >
                <div className="flex flex-wrap items-center gap-2 text-[0.68rem] text-ink-muted">
                  <span
                    className="rounded px-1.5 py-0.5 text-[0.64rem] font-bold uppercase"
                    style={{ backgroundColor: `${catColor}22`, color: catColor }}
                  >
                    {post.category}
                  </span>
                  <span>{formatDate(post.date_created)}</span>
                </div>
                <div className="grid gap-3 sm:grid-cols-[1fr_auto] sm:items-center">
                  <div>
                    <h3 className="mb-1 text-sm font-bold text-ink group-hover:text-accent transition-colors">{post.title}</h3>
                    <p className="text-[0.82rem] leading-relaxed text-ink-muted line-clamp-3">{stripHtml(post.content).slice(0, 160)}</p>
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
        <div className="grid min-h-[200px] place-items-center rounded-lg border border-dashed border-border bg-surface-elevated/20">
          <div className="text-center">
            <MessageSquareQuote size={32} className="mx-auto mb-2 text-ink-muted/40" />
            <p className="text-sm text-ink-muted">아직 게시글이 없습니다.</p>
          </div>
        </div>
      )}
    </section>
  );
}
