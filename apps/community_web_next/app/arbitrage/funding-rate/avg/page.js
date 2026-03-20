import { buildMetadata } from "../../../../lib/site";
import ArbitrageAverageFundingRateClient from "../../../../components/arbitrage/ArbitrageAverageFundingRateClient";

export const metadata = buildMetadata({
  title: "평균 펀딩비 | 거래소별 펀딩비 추이",
  description: "거래소별 평균 펀딩비 추이와 변동을 한눈에 확인하세요.",
  pathname: "/arbitrage/funding-rate/avg",
});

export default function AverageFundingRatePage() {
  return <ArbitrageAverageFundingRateClient />;
}
