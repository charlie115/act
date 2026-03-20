"use client";

import { useEffect, useState } from "react";
import { Ticket } from "lucide-react";
import { useAuth } from "../auth/AuthProvider";

export default function CouponDashboardClient() {
  const { authorizedRequest, loggedIn } = useAuth();
  const [coupons, setCoupons] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!loggedIn) return;
    authorizedRequest("/coupon/coupons/")
      .then((data) => setCoupons(Array.isArray(data) ? data : data?.results || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [loggedIn, authorizedRequest]);

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <h1 className="text-2xl font-bold text-ink">쿠폰 관리</h1>
      <div className="rounded-lg border border-border bg-surface p-6">
        {loading ? (
          <div className="grid place-items-center py-12">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-border border-t-accent" />
          </div>
        ) : coupons.length === 0 ? (
          <div className="grid place-items-center py-12 text-ink-muted">
            <Ticket size={32} className="mb-2 opacity-40" />
            <p className="text-sm">등록된 쿠폰이 없습니다.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {coupons.map((coupon) => (
              <div key={coupon.id} className="flex items-center justify-between rounded-lg border border-border/50 bg-background p-4">
                <div>
                  <p className="font-semibold text-ink">{coupon.code}</p>
                  <p className="text-xs text-ink-muted">{coupon.description || "쿠폰"}</p>
                </div>
                <span className={`rounded-full px-3 py-1 text-xs font-bold ${coupon.used ? "bg-border/30 text-ink-muted" : "bg-positive/20 text-positive"}`}>
                  {coupon.used ? "사용됨" : "미사용"}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
