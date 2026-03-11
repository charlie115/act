import Link from "next/link";
import { redirect } from "next/navigation";

import AffiliateDashboardClient from "../../../components/affiliate/AffiliateDashboardClient";
import CommissionHistoryClient from "../../../components/affiliate/CommissionHistoryClient";
import RequireAuth from "../../../components/auth/RequireAuth";
import { buildMetadata } from "../../../lib/site";

export const metadata = buildMetadata({
  title: "Affiliate",
  description: "Affiliate dashboard와 commission history를 Next 앱에서 제공합니다.",
  pathname: "/affiliate",
});

export default function AffiliatePage({ params }) {
  const slug = params?.slug || [];
  const currentTab = slug[0] || null;

  if (!currentTab) {
    redirect("/affiliate/dashboard");
  }

  return (
    <RequireAuth>
      <div className="section-stack">
        <section className="surface-card">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Affiliate</p>
              <h1>제휴 대시보드</h1>
            </div>
            <div className="tab-strip">
              <Link className={`tab-pill${currentTab === "dashboard" ? " tab-pill--active" : ""}`} href="/affiliate/dashboard">
                Dashboard
              </Link>
              <Link
                className={`tab-pill${currentTab === "commission-history" ? " tab-pill--active" : ""}`}
                href="/affiliate/commission-history"
              >
                Commission History
              </Link>
            </div>
          </div>
        </section>

        {currentTab === "dashboard" ? <AffiliateDashboardClient /> : null}
        {currentTab === "commission-history" ? <CommissionHistoryClient /> : null}
      </div>
    </RequireAuth>
  );
}
