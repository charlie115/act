import { buildMetadata } from "../../lib/site";
import LegacyNewsClient from "../../components/legacy/LegacyNewsClient";

export const metadata = buildMetadata({
  title: "News",
  description: "뉴스, SNS, 거래소 공지를 Next 앱에서 필터링 가능한 허브 화면으로 제공합니다.",
  pathname: "/news",
});

export default function NewsPage() {
  return <LegacyNewsClient />;
}
