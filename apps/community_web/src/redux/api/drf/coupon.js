import drfApi from 'redux/api/drf';

const couponApi = drfApi.injectEndpoints({
  endpoints: (builder) => ({
    getCoupons: builder.query({
      query: () => ({ url: '/coupon/coupons/' }), 
      // Assumes /coupon/ is a GET endpoint that returns a list of coupons
    }),
    getCouponRedemptions: builder.query({
      query: () => ({ url: '/coupon/coupon-redemption/' }), 
      // Assumes /coupon/ is a GET endpoint that returns a list of coupon redemptions
    }),
    redeemCoupon: builder.mutation({
      query: (body) => ({ url: '/coupon/coupon-redemption/redeem/', method: 'POST', body }),
      invalidatesTags: ['CouponRedemption'], // adjust tag names as needed
    }),
  }),
});

export const {
  useGetCouponsQuery,
  useLazyGetCouponsQuery,
  useRedeemCouponMutation,
  useGetCouponRedemptionsQuery,
} = couponApi;

export default couponApi;