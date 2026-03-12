"use client";

import { useEffect, useMemo, useState } from "react";

import { useAuth } from "../auth/AuthProvider";
import SurfaceNotice from "../ui/SurfaceNotice";

function formatAmount(value) {
  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 0,
  }).format(Number(value || 0));
}

export default function CouponDashboardClient() {
  const { authorizedListRequest, authorizedRequest } = useAuth();
  const [coupons, setCoupons] = useState([]);
  const [redemptions, setRedemptions] = useState([]);
  const [isBusy, setIsBusy] = useState(false);
  const [pageError, setPageError] = useState("");

  useEffect(() => {
    let active = true;

    async function loadPage() {
      setPageError("");

      try {
        const [nextCoupons, nextRedemptions] = await Promise.all([
          authorizedListRequest("/coupon/coupons/"),
          authorizedListRequest("/coupon/coupon-redemption/"),
        ]);

        if (!active) {
          return;
        }

        setCoupons(nextCoupons);
        setRedemptions(nextRedemptions);
      } catch (requestError) {
        if (!active) {
          return;
        }

        setPageError(requestError.message || "쿠폰 대시보드를 불러오지 못했습니다.");
      }
    }

    loadPage();

    return () => {
      active = false;
    };
  }, [authorizedListRequest]);

  const redeemedCouponNames = useMemo(
    () => new Set(redemptions.map((item) => item.coupon)),
    [redemptions]
  );

  async function handleRedeem(name) {
    setIsBusy(true);
    setPageError("");

    try {
      await authorizedRequest("/coupon/coupon-redemption/redeem/", {
        method: "POST",
        body: { name },
      });

      const nextRedemptions = await authorizedListRequest("/coupon/coupon-redemption/");
      setRedemptions(nextRedemptions);
    } catch (requestError) {
      setPageError(requestError.payload?.message || "쿠폰 사용 처리에 실패했습니다.");
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <section className="surface-card">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Coupons</p>
          <h1>쿠폰 대시보드</h1>
        </div>
      </div>

      <div className="coupon-stack">
        {coupons.length ? (
          coupons.map((coupon) => {
            const isRedeemed = redeemedCouponNames.has(coupon.name);

            return (
              <article
                key={coupon.id}
                className={`coupon-card${isRedeemed ? " coupon-card--used" : ""}`}
              >
                <div>
                  <h2>
                    {coupon.name} - {formatAmount(coupon.amount)} USDT
                  </h2>
                  <p className="muted-copy">
                    {coupon.expires_at
                      ? `만료 시각 ${new Date(coupon.expires_at).toLocaleString()}`
                      : "만료 기한 없음"}
                  </p>
                </div>
                <div>
                  {isRedeemed ? (
                    <button className="ghost-button ghost-button--button" disabled type="button">
                      사용 완료
                    </button>
                  ) : (
                    <button
                      className="primary-button ghost-button--button"
                      disabled={isBusy}
                      onClick={() => handleRedeem(coupon.name)}
                      type="button"
                    >
                      {isBusy ? "사용 처리 중..." : "쿠폰 사용"}
                    </button>
                  )}
                </div>
              </article>
            );
          })
        ) : (
          <div className="empty-state">사용 가능한 쿠폰이 없습니다.</div>
        )}
      </div>

      {pageError ? <SurfaceNotice description={pageError} variant="error" /> : null}
    </section>
  );
}
