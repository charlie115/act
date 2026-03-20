import CouponDashboardClient from "../../components/coupon/CouponDashboardClient";
import RequireAuth from "../../components/auth/RequireAuth";
import { buildMetadata } from "../../lib/site";

export const metadata = buildMetadata({
  title: "Coupon Dashboard",
  description: "쿠폰 관리 및 사용 내역을 확인하세요.",
  pathname: "/coupon-dashboard",
});

export default function CouponDashboardPage() {
  return (
    <RequireAuth>
      <CouponDashboardClient />
    </RequireAuth>
  );
}
