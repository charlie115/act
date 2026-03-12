"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { usePathname, useRouter } from "next/navigation";

import { useAuth } from "../auth/AuthProvider";
import { formatDate, safeHtml } from "../../lib/api";
import { fetchCachedJson } from "../../lib/clientCache";
import { USER_ROLE } from "../../lib/constants";
import SurfaceNotice from "../ui/SurfaceNotice";

function canModerate(user, authorProfile, authorId) {
  if (!user) {
    return false;
  }

  if (user.role === USER_ROLE.admin || user.role === USER_ROLE.internal) {
    return true;
  }

  return Boolean(user.uuid && authorId && user.uuid === authorId) ||
    Boolean(user.username && user.username === authorProfile?.username);
}

function ReactionRow({ counts, currentReaction, disabled, onToggle }) {
  return (
    <div className="reaction-row">
      <button
        className={`reaction-pill${currentReaction === "LIKE" ? " reaction-pill--active" : ""}`}
        disabled={disabled}
        onClick={() => onToggle("LIKE")}
        type="button"
      >
        좋아요 {counts.likes ?? 0}
      </button>
      <button
        className={`reaction-pill${currentReaction === "DISLIKE" ? " reaction-pill--active" : ""}`}
        disabled={disabled}
        onClick={() => onToggle("DISLIKE")}
        type="button"
      >
        싫어요 {counts.dislikes ?? 0}
      </button>
    </div>
  );
}

function CommentThread({
  comment,
  depth = 0,
  disabled,
  onDelete,
  onReact,
  onReply,
  user,
}) {
  const [replyOpen, setReplyOpen] = useState(false);
  const [reply, setReply] = useState("");

  return (
    <li className="comment-thread__item" style={{ "--depth": depth }}>
      <div className="comment-thread__meta">
        <strong>{comment.author_profile?.username || "Anonymous"}</strong>
        <span>{formatDate(comment.date_created)}</span>
      </div>
      <p>{comment.content}</p>
      <div className="comment-actions">
        <ReactionRow
          counts={comment}
          currentReaction={comment.user_reaction?.reaction}
          disabled={disabled}
          onToggle={(reaction) => onReact(comment, reaction)}
        />
        {user ? (
          <button
            className="ghost-button ghost-button--button small-button"
            onClick={() => setReplyOpen((current) => !current)}
            type="button"
          >
            답글
          </button>
        ) : null}
        {canModerate(user, comment.author_profile, comment.author) ? (
          <button
            className="ghost-button ghost-button--button small-button"
            disabled={disabled}
            onClick={() => onDelete(comment.id)}
            type="button"
          >
            삭제
          </button>
        ) : null}
      </div>
      {replyOpen ? (
        <form
          className="auth-form"
          onSubmit={async (event) => {
            event.preventDefault();
            await onReply(comment.id, reply);
            setReply("");
            setReplyOpen(false);
          }}
        >
          <textarea
            className="auth-form__textarea"
            onChange={(event) => setReply(event.target.value)}
            placeholder="답글을 입력하세요"
            rows={3}
            value={reply}
          />
          <button
            className="primary-button ghost-button--button"
            disabled={!reply.trim() || disabled}
            type="submit"
          >
            답글 등록
          </button>
        </form>
      ) : null}
      {comment.replies?.length ? (
        <ul className="comment-thread">
          {comment.replies.map((replyItem) => (
            <CommentThread
              key={replyItem.id}
              comment={replyItem}
              depth={depth + 1}
              disabled={disabled}
              onDelete={onDelete}
              onReact={onReact}
              onReply={onReply}
              user={user}
            />
          ))}
        </ul>
      ) : null}
    </li>
  );
}

export default function BoardPostClient({ postId }) {
  const pathname = usePathname();
  const router = useRouter();
  const { authorizedRequest, isReady, loggedIn, user } = useAuth();
  const [post, setPost] = useState(null);
  const [comments, setComments] = useState([]);
  const [pageError, setPageError] = useState("");
  const [isBusy, setIsBusy] = useState(false);
  const [comment, setComment] = useState("");

  function countCommentsTree(items) {
    return items.reduce(
      (sum, item) => sum + 1 + countCommentsTree(item.replies || []),
      0
    );
  }

  useEffect(() => {
    let active = true;

    async function loadPost() {
      setPageError("");

      try {
        const fetchPost = loggedIn
          ? authorizedRequest(`/board/posts/${postId}/`)
          : fetchCachedJson(`/api/board/posts/${postId}/`, { ttlMs: 10000 });
        const fetchComments = loggedIn
          ? authorizedRequest(`/board/comments/?post=${postId}`)
          : fetchCachedJson(`/api/board/comments/?post=${postId}`, { ttlMs: 10000 });

        const [postPayload, commentsPayload] = await Promise.all([fetchPost, fetchComments]);

        if (!active) return;

        setPost(postPayload);
        setComments(commentsPayload.results || commentsPayload || []);
      } catch (requestError) {
        if (!active) return;
        setPageError(requestError.message || "게시글을 불러오지 못했습니다.");
      }
    }

    if (isReady) loadPost();

    return () => {
      active = false;
    };
  }, [authorizedRequest, isReady, loggedIn, postId]);

  useEffect(() => {
    async function recordView() {
      if (!loggedIn || !user?.uuid || !post?.id) return;
      try {
        if (post.user_view) {
          const lastView = new Date(post.user_view);
          const now = new Date();
          const lastKst = new Date(lastView.toLocaleString("en-US", { timeZone: "Asia/Seoul" }));
          const nowKst = new Date(now.toLocaleString("en-US", { timeZone: "Asia/Seoul" }));
          const startOfDayKst = new Date(nowKst);
          startOfDayKst.setHours(0, 0, 0, 0);

          if (lastKst >= startOfDayKst) {
            return;
          }
        }

        await authorizedRequest("/board/post-views/", {
          method: "POST",
          body: { post: post.id, user: user.uuid },
        });
      } catch {
        // ignore
      }
    }

    recordView();
  }, [authorizedRequest, loggedIn, post?.id, post?.user_view, user?.uuid]);

  const canDeletePost = useMemo(
    () => canModerate(user, post?.author_profile, post?.author),
    [post?.author, post?.author_profile, user]
  );

  async function reloadPost() {
    const postPayload = await (loggedIn
      ? authorizedRequest(`/board/posts/${postId}/`)
      : fetchCachedJson(`/api/board/posts/${postId}/`, { ttlMs: 10000 }));
    setPost(postPayload);
    return postPayload;
  }

  async function reloadComments() {
    const commentsPayload = await (loggedIn
      ? authorizedRequest(`/board/comments/?post=${postId}`)
      : fetchCachedJson(`/api/board/comments/?post=${postId}`, { ttlMs: 10000 }));
    const nextComments = commentsPayload.results || commentsPayload || [];
    setComments(nextComments);
    setPost((current) =>
      current ? { ...current, comments: countCommentsTree(nextComments) } : current
    );
    return nextComments;
  }

  async function handlePostReaction(reaction) {
    if (!loggedIn || !post) return;
    setIsBusy(true);
    setPageError("");
    try {
      if (post.user_reaction) {
        if (post.user_reaction.reaction === reaction) {
          await authorizedRequest(`/board/post-reactions/${post.user_reaction.id}/`, {
            method: "DELETE",
          });
        } else {
          await authorizedRequest(`/board/post-reactions/${post.user_reaction.id}/`, {
            method: "PATCH",
            body: { reaction },
          });
        }
      } else {
        await authorizedRequest("/board/post-reactions/", {
          method: "POST",
          body: { post: post.id, user: user.uuid, reaction },
        });
      }
      await reloadPost();
    } catch (requestError) {
      setPageError(requestError.message || "반응 업데이트에 실패했습니다.");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleCommentSubmit(parent = null, content = comment) {
    if (!loggedIn || !content.trim()) return;
    setIsBusy(true);
    setPageError("");
    try {
      await authorizedRequest("/board/comments/", {
        method: "POST",
        body: { author: user.uuid, post: post.id, parent, content },
      });
      setComment("");
      await reloadComments();
    } catch (requestError) {
      setPageError(requestError.message || "댓글 작성에 실패했습니다.");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleCommentReaction(commentItem, reaction) {
    if (!loggedIn) return;
    setIsBusy(true);
    setPageError("");
    try {
      if (commentItem.user_reaction) {
        if (commentItem.user_reaction.reaction === reaction) {
          await authorizedRequest(`/board/comment-reactions/${commentItem.user_reaction.id}/`, {
            method: "DELETE",
          });
        } else {
          await authorizedRequest(`/board/comment-reactions/${commentItem.user_reaction.id}/`, {
            method: "PATCH",
            body: { reaction },
          });
        }
      } else {
        await authorizedRequest("/board/comment-reactions/", {
          method: "POST",
          body: { comment: commentItem.id, user: user.uuid, reaction },
        });
      }
      await reloadComments();
    } catch (requestError) {
      setPageError(requestError.message || "댓글 반응 업데이트에 실패했습니다.");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleDeleteComment(commentId) {
    setIsBusy(true);
    setPageError("");
    try {
      await authorizedRequest(`/board/comments/${commentId}/`, { method: "DELETE" });
      await reloadComments();
    } catch (requestError) {
      setPageError(requestError.message || "댓글 삭제에 실패했습니다.");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleDeletePost() {
    if (!post) return;
    setIsBusy(true);
    setPageError("");
    try {
      await authorizedRequest(`/board/posts/${post.id}/`, { method: "DELETE" });
      router.replace("/community-board");
    } catch (requestError) {
      setPageError(requestError.message || "게시글 삭제에 실패했습니다.");
    } finally {
      setIsBusy(false);
    }
  }

  if (!post) {
    return (
      <section className="surface-card">
        <SurfaceNotice
          description="게시글 내용을 불러오는 중입니다."
          title="게시글 로딩 중"
          variant={pageError ? "error" : "loading"}
        />
        {pageError ? <SurfaceNotice description={pageError} variant="error" /> : null}
      </section>
    );
  }

  return (
    <article className="surface-card post-detail">
      <div className="post-detail__header">
        <div className="post-detail__meta">
          <span>{post.category}</span>
          <span>{formatDate(post.date_created)}</span>
        </div>
        <h1>{post.title}</h1>
        <div className="post-detail__stats">
          <span>작성자 {post.author_profile?.username || "Unknown"}</span>
          <span>댓글 {post.comments}</span>
          <span>조회 {post.views}</span>
          <span>좋아요 {post.likes}</span>
          <span>싫어요 {post.dislikes}</span>
        </div>
      </div>

      <div className="post-detail__toolbar">
        <Link className="ghost-button" href="/community-board">
          Back
        </Link>
        {canDeletePost ? (
          <button
            className="ghost-button ghost-button--button"
            disabled={isBusy}
            onClick={handleDeletePost}
            type="button"
          >
            삭제
          </button>
        ) : null}
      </div>

      <div className="rich-content" dangerouslySetInnerHTML={{ __html: safeHtml(post.content) }} />

      {loggedIn ? (
        <ReactionRow
          counts={post}
          currentReaction={post.user_reaction?.reaction}
          disabled={isBusy}
          onToggle={handlePostReaction}
        />
      ) : null}

      <section className="comments-panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Comments</p>
            <h2>댓글</h2>
          </div>
          <span>{countCommentsTree(comments)} items</span>
        </div>

        {loggedIn ? (
          <form
            className="auth-form"
            onSubmit={async (event) => {
              event.preventDefault();
              await handleCommentSubmit();
            }}
          >
            <textarea
              className="auth-form__textarea"
              onChange={(event) => setComment(event.target.value)}
              placeholder="댓글을 입력하세요"
              rows={4}
              value={comment}
            />
            <button
              className="primary-button ghost-button--button"
              disabled={!comment.trim() || isBusy}
              type="submit"
            >
              댓글 등록
            </button>
          </form>
        ) : (
          <div className="inline-note">
            댓글 작성은{" "}
            <Link className="inline-link" href={`/login?next=${encodeURIComponent(pathname)}`}>
              로그인
            </Link>
            {" "}후 가능합니다.
          </div>
        )}

        {comments.length ? (
          <ul className="comment-thread">
            {comments.map((commentItem) => (
              <CommentThread
                key={commentItem.id}
                comment={commentItem}
                disabled={isBusy}
                onDelete={handleDeleteComment}
                onReact={handleCommentReaction}
                onReply={handleCommentSubmit}
                user={user}
              />
            ))}
          </ul>
        ) : (
          <p className="muted-copy">아직 댓글이 없습니다.</p>
        )}
      </section>

      {pageError ? <SurfaceNotice description={pageError} variant="error" /> : null}
    </article>
  );
}
