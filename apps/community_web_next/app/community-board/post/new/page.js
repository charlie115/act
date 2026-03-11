import RequireAuth from "../../../../components/auth/RequireAuth";
import BoardPostEditorClient from "../../../../components/board/BoardPostEditorClient";
import { buildMetadata } from "../../../../lib/site";

export const metadata = {
  ...buildMetadata({
    title: "New Board Post",
    description: "커뮤니티 게시판에 새 글을 작성합니다.",
    pathname: "/community-board/post/new",
  }),
  robots: {
    index: false,
    follow: false,
  },
};

export default function CommunityBoardPostNewPage() {
  return (
    <RequireAuth>
      <BoardPostEditorClient />
    </RequireAuth>
  );
}
