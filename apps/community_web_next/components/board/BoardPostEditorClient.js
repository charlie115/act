"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../auth/AuthProvider";

export default function BoardPostEditorClient({ post = null }) {
  const { authorizedRequest } = useAuth();
  const router = useRouter();
  const [title, setTitle] = useState(post?.title || "");
  const [content, setContent] = useState(post?.content || "");
  const [submitting, setSubmitting] = useState(false);

  const isEdit = Boolean(post);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title.trim() || !content.trim()) return;
    setSubmitting(true);
    try {
      if (isEdit) {
        await authorizedRequest(`/board/posts/${post.id}/`, { method: "PATCH", body: { title, content } });
        router.push(`/community-board/post/${post.id}`);
      } else {
        const created = await authorizedRequest("/board/posts/", { method: "POST", body: { title, content } });
        router.push(`/community-board/post/${created.id}`);
      }
    } catch {
      alert("저장에 실패했습니다.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <h1 className="text-2xl font-bold text-ink">{isEdit ? "게시글 수정" : "새 게시글"}</h1>
      <form onSubmit={handleSubmit} className="rounded-xl border border-border bg-surface p-6 space-y-4">
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="제목"
          className="w-full rounded-lg border border-border bg-background px-4 py-3 text-ink placeholder:text-ink-muted/50 focus:border-accent focus:outline-none"
        />
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="내용을 입력하세요"
          rows={12}
          className="w-full rounded-lg border border-border bg-background px-4 py-3 text-sm text-ink placeholder:text-ink-muted/50 focus:border-accent focus:outline-none resize-none"
        />
        <div className="flex justify-end gap-3">
          <button
            type="button"
            onClick={() => router.back()}
            className="rounded-lg border border-border px-4 py-2 text-sm text-ink-muted hover:bg-surface-elevated"
          >
            취소
          </button>
          <button
            type="submit"
            disabled={submitting}
            className="rounded-lg bg-accent px-6 py-2 text-sm font-bold text-white hover:bg-accent/80 disabled:opacity-50"
          >
            {submitting ? "저장 중..." : isEdit ? "수정" : "등록"}
          </button>
        </div>
      </form>
    </div>
  );
}
