import LegacyHomeClient from "../components/legacy/LegacyHomeClient";
import { buildMetadata } from "../lib/site";

export const metadata = buildMetadata({
  title: "Home",
  description:
    "ArbiCrypto 홈 화면. 실시간 프리미엄 데이터와 시장 조합 탐색을 Next.js 환경에서 제공합니다.",
  pathname: "/",
});

export default function HomePage() {
  return (
    <div className="section-stack">
      <LegacyHomeClient />
    </div>
  );
}
