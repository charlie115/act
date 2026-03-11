import RequireAuth from "../../components/auth/RequireAuth";
import MyPageClient from "../../components/mypage/MyPageClient";
import { buildMetadata } from "../../lib/site";

export const metadata = buildMetadata({
  title: "My Page",
  description: "개인 설정 페이지는 Next 전환 2단계 대상입니다.",
  pathname: "/my-page",
});

export default function MyPage() {
  return (
    <RequireAuth>
      <MyPageClient />
    </RequireAuth>
  );
}
