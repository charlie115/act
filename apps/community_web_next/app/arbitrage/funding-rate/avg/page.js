import { buildMetadata } from "../../../../lib/site";
import ArbitrageAverageFundingRateClient from "../../../../components/arbitrage/ArbitrageAverageFundingRateClient";

export const metadata = buildMetadata({
  title: "Average Funding Rate",
  description: "최근 funding rate 평균값을 Next 앱에서 읽기 전용 테이블로 제공합니다.",
  pathname: "/arbitrage/funding-rate/avg",
});

export default function AverageFundingRatePage() {
  return <ArbitrageAverageFundingRateClient />;
}
