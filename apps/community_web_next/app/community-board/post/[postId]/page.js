import Link from "next/link";
import { notFound } from "next/navigation";

import BoardPostDetail from "../../../../components/BoardPostDetail";
import { getBoardComments, getBoardPost, stripHtml } from "../../../../lib/api";
import { buildMetadata } from "../../../../lib/site";

export const dynamic = "force-dynamic";

export async function generateMetadata({ params }) {
  const post = await getBoardPost(params.postId).catch(() => null);

  if (!post) {
    return buildMetadata({
      title: "Post Not Found",
      description: "요청한 게시글을 찾을 수 없습니다.",
      pathname: `/community-board/post/${params.postId}`,
      type: "article",
    });
  }

  return buildMetadata({
    title: post.title,
    description: stripHtml(post.content).slice(0, 160),
    pathname: `/community-board/post/${post.id}`,
    type: "article",
  });
}

export default async function CommunityBoardPostPage({ params }) {
  const [post, comments] = await Promise.all([
    getBoardPost(params.postId).catch(() => null),
    getBoardComments(params.postId).catch(() => []),
  ]);

  if (!post) {
    notFound();
  }

  return (
    <div className="section-stack">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Community Board</p>
          <h1>게시글 상세</h1>
        </div>
        <Link className="ghost-button" href="/community-board">
          목록으로 돌아가기
        </Link>
      </div>
      <BoardPostDetail comments={comments} post={post} />
    </div>
  );
}
