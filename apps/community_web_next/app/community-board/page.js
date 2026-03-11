import Link from "next/link";

import { formatDate, getBoardPosts, stripHtml } from "../../lib/api";
import { buildMetadata } from "../../lib/site";

export const dynamic = "force-dynamic";

export const metadata = buildMetadata({
  title: "Community Board",
  description: "ACW 커뮤니티 게시판을 서버 렌더링으로 제공하는 공개 보드 페이지입니다.",
  pathname: "/community-board",
});

export default async function CommunityBoardPage({ searchParams }) {
  const category = searchParams?.category || undefined;
  const page = searchParams?.page || undefined;

  const board = await getBoardPosts({ category, page }).catch(() => ({
    count: 0,
    results: [],
  }));

  return (
    <section className="surface-card">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Community Board</p>
          <h1>공지와 커뮤니티 대화</h1>
        </div>
        <span>{board.count} posts</span>
      </div>
      {board.results.length ? (
        <div className="board-grid">
          {board.results.map((post) => (
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
              <p>{stripHtml(post.content).slice(0, 180)}</p>
              <div className="board-grid__stats">
                <span>{post.comments} comments</span>
                <span>{post.views} views</span>
                <span>{post.likes} likes</span>
                <span>{post.dislikes} dislikes</span>
              </div>
            </Link>
          ))}
        </div>
      ) : (
        <div className="empty-state">게시글을 불러오지 못했습니다.</div>
      )}
    </section>
  );
}
