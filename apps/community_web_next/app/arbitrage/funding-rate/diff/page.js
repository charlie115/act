import { buildMetadata } from "../../../../lib/site";
import ArbitrageFundingRateDiffClient from "../../../../components/arbitrage/ArbitrageFundingRateDiffClient";

export const metadata = buildMetadata({
  title: "펀딩비 차이 비교 | 거래소별 실시간",
  description: "바이낸스, OKX, 바이빗 등 거래소별 펀딩비 차이를 실시간으로 비교 분석합니다.",
  pathname: "/arbitrage/funding-rate/diff",
});

export default function FundingRateDiffPage() {
  return <ArbitrageFundingRateDiffClient />;
}
