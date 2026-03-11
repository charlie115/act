import BoardListClient from "../../components/board/BoardListClient";
import { getBoardPosts } from "../../lib/api";
import { buildMetadata } from "../../lib/site";

export const metadata = buildMetadata({
  title: "Community Board",
  description: "ACW 커뮤니티 게시판을 서버 렌더링으로 제공하는 공개 보드 페이지입니다.",
  pathname: "/community-board",
});

export default async function CommunityBoardPage({ searchParams }) {
  const resolvedSearchParams = await searchParams;
  const category = resolvedSearchParams?.category || undefined;
  const currentPage = Number(resolvedSearchParams?.page || 1);
  const page = currentPage || undefined;

  const board = await getBoardPosts({ category, page }).catch(() => ({
    count: 0,
    results: [],
  }));

  return (
    <BoardListClient
      count={board.count}
      currentCategory={category || ""}
      currentPage={currentPage}
      posts={board.results}
    />
  );
}
