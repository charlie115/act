import RequireAuth from "../../components/auth/RequireAuth";
import AffiliateRequestClient from "../../components/affiliate/AffiliateRequestClient";
import { buildMetadata } from "../../lib/site";

export const metadata = buildMetadata({
  title: "Request Affiliate",
  description: "제휴사 신청 페이지입니다.",
  pathname: "/request-affiliate",
});

export default function RequestAffiliatePage() {
  return (
    <RequireAuth>
      <AffiliateRequestClient />
    </RequireAuth>
  );
}
