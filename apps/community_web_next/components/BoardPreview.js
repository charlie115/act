import Link from "next/link";

import { formatDate, stripHtml } from "../lib/api";

export default function BoardPreview({ posts = [] }) {
  return (
    <section className="surface-card">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Community Board</p>
          <h2>최근 커뮤니티 업데이트</h2>
        </div>
        <Link href="/community-board">게시판 이동</Link>
      </div>
      <div className="board-grid">
        {posts.map((post) => (
          <Link
            key={post.id}
            className="board-grid__item"
            href={`/community-board/post/${post.id}`}
          >
            <div className="board-grid__meta">
              <span>{post.category}</span>
              <span>{formatDate(post.date_created)}</span>
            </div>
            <h3>{post.title}</h3>
            <p>{stripHtml(post.content).slice(0, 160)}</p>
            <div className="board-grid__stats">
              <span>{post.comments} comments</span>
              <span>{post.views} views</span>
              <span>{post.likes} likes</span>
            </div>
          </Link>
        ))}
      </div>
    </section>
  );
}
