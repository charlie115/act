import RequireAuth from "../../components/auth/RequireAuth";
import AffiliateRequestClient from "../../components/affiliate/AffiliateRequestClient";
import { buildMetadata } from "../../lib/site";

export const metadata = buildMetadata({
  title: "Request Affiliate",
  description: "제휴 신청 폼은 차후 Next 앱으로 이전됩니다.",
  pathname: "/request-affiliate",
});

export default function RequestAffiliatePage() {
  return (
    <RequireAuth>
      <AffiliateRequestClient />
    </RequireAuth>
  );
}
