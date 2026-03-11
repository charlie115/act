import CouponDashboardClient from "../../components/coupon/CouponDashboardClient";
import RequireAuth from "../../components/auth/RequireAuth";
import { buildMetadata } from "../../lib/site";

export const metadata = buildMetadata({
  title: "Coupon Dashboard",
  description: "쿠폰 대시보드 영역은 아직 이전 전입니다.",
  pathname: "/coupon-dashboard",
});

export default function CouponDashboardPage() {
  return (
    <RequireAuth>
      <CouponDashboardClient />
    </RequireAuth>
  );
}
