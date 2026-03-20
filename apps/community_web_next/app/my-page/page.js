import RequireAuth from "../../components/auth/RequireAuth";
import MyPageClient from "../../components/mypage/MyPageClient";
import { buildMetadata } from "../../lib/site";

export const metadata = buildMetadata({
  title: "My Page",
  description: "개인 설정 및 계정 관리 페이지입니다.",
  pathname: "/my-page",
});

export default function MyPage() {
  return (
    <RequireAuth>
      <MyPageClient />
    </RequireAuth>
  );
}
