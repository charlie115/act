import { formatDate, safeHtml } from "../lib/api";

function Comment({ comment, depth = 0 }) {
  return (
    <li className="comment-thread__item" style={{ "--depth": depth }}>
      <div className="comment-thread__meta">
        <strong>{comment.author_profile?.username || "Anonymous"}</strong>
        <span>{formatDate(comment.date_created)}</span>
      </div>
      <p>{comment.content}</p>
      {comment.replies?.length ? (
        <ul className="comment-thread">
          {comment.replies.map((reply) => (
            <Comment key={reply.id} comment={reply} depth={depth + 1} />
          ))}
        </ul>
      ) : null}
    </li>
  );
}

export default function BoardPostDetail({ post, comments }) {
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
        </div>
      </div>
      <div
        className="rich-content"
        dangerouslySetInnerHTML={{ __html: safeHtml(post.content) }}
      />
      <section className="comments-panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Comments</p>
            <h2>댓글</h2>
          </div>
          <span>{comments.length} items</span>
        </div>
        {comments.length ? (
          <ul className="comment-thread">
            {comments.map((comment) => (
              <Comment key={comment.id} comment={comment} />
            ))}
          </ul>
        ) : (
          <p className="muted-copy">아직 댓글이 없습니다.</p>
        )}
      </section>
    </article>
  );
}
