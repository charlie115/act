"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, Trash2 } from "lucide-react";
import Link from "next/link";
import { useAuth } from "../auth/AuthProvider";
import { getPost, getComments } from "../../lib/board";

export default function BoardPostClient({ postId }) {
  const { user, loggedIn, authorizedRequest } = useAuth();
  const router = useRouter();
  const [post, setPost] = useState(null);
  const [comments, setComments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [commentText, setCommentText] = useState("");

  useEffect(() => {
    Promise.all([getPost(postId), getComments(postId)])
      .then(([p, c]) => { setPost(p); setComments(c); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [postId]);

  const handleDelete = async () => {
    if (!confirm("정말 삭제하시겠습니까?")) return;
    await authorizedRequest(`/board/posts/${postId}/`, { method: "DELETE" });
    router.push("/community-board");
  };

  const handleComment = async (e) => {
    e.preventDefault();
    if (!commentText.trim()) return;
    await authorizedRequest(`/board/posts/${postId}/comments/`, {
      method: "POST",
      body: { content: commentText },
    });
    setCommentText("");
    const c = await getComments(postId);
    setComments(c);
  };

  if (loading) {
    return <div className="grid min-h-[40vh] place-items-center"><div className="h-8 w-8 animate-spin rounded-full border-2 border-border border-t-accent" /></div>;
  }
  if (!post) return <p className="text-ink-muted py-12 text-center">게시글을 찾을 수 없습니다.</p>;

  const isAuthor = loggedIn && user?.id === post.author?.id;

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <Link href="/community-board" className="inline-flex items-center gap-1 text-sm text-ink-muted hover:text-ink">
        <ArrowLeft size={14} /> 목록으로
      </Link>
      <article className="rounded-xl border border-border bg-surface p-6 space-y-4">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-xl font-bold text-ink">{post.title}</h1>
            <p className="mt-1 text-xs text-ink-muted">{post.author?.email?.split("@")[0]} · {new Date(post.date_created).toLocaleDateString("ko-KR")}</p>
          </div>
          {isAuthor && (
            <div className="flex gap-2">
              <button onClick={handleDelete} className="text-ink-muted hover:text-negative" type="button"><Trash2 size={16} /></button>
            </div>
          )}
        </div>
        <div className="prose prose-invert max-w-none text-sm text-ink" dangerouslySetInnerHTML={{ __html: post.content }} />
      </article>

      <div className="rounded-xl border border-border bg-surface p-6 space-y-4">
        <h2 className="text-sm font-semibold text-ink">댓글 ({comments.length})</h2>
        {loggedIn && (
          <form onSubmit={handleComment} className="flex gap-2">
            <input
              value={commentText}
              onChange={(e) => setCommentText(e.target.value)}
              placeholder="댓글을 입력하세요"
              className="flex-1 rounded-lg border border-border bg-background px-3 py-2 text-sm text-ink placeholder:text-ink-muted/50 focus:border-accent focus:outline-none"
            />
            <button type="submit" className="rounded-lg bg-accent px-4 py-2 text-sm font-bold text-white hover:bg-accent/80">등록</button>
          </form>
        )}
        <div className="space-y-3">
          {comments.map((c) => (
            <div key={c.id} className="border-b border-border/30 pb-3">
              <p className="text-xs text-ink-muted">{c.author?.email?.split("@")[0]} · {new Date(c.date_created).toLocaleDateString("ko-KR")}</p>
              <p className="mt-1 text-sm text-ink">{c.content}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
