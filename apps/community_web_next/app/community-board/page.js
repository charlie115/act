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
  const page = Number(resolvedSearchParams?.page || 1);
  const boardData = await getBoardPosts({
    category,
    page,
    page_size: 20,
  });

  return (
    <BoardListClient
      count={boardData.count}
      currentCategory={category || ""}
      currentPage={page}
      posts={boardData.results}
    />
  );
}
