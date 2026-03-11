import { buildMetadata } from "../../../../lib/site";
import ArbitrageFundingRateDiffClient from "../../../../components/arbitrage/ArbitrageFundingRateDiffClient";

export const metadata = buildMetadata({
  title: "Funding Rate Difference",
  description: "거래소 간 funding rate 차이를 Next 앱에서 읽기 전용 테이블로 제공합니다.",
  pathname: "/arbitrage/funding-rate/diff",
});

export default function FundingRateDiffPage() {
  return <ArbitrageFundingRateDiffClient />;
}
