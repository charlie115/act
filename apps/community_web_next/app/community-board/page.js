import BoardListClient from "../../components/board/BoardListClient";
import { getBoardPosts } from "../../lib/api";
import { buildMetadata } from "../../lib/site";

export const metadata = buildMetadata({
  title: "커뮤니티 게시판",
  description: "암호화폐 차익거래 커뮤니티. 김프 분석, 거래 전략, 시장 토론에 참여하세요.",
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
