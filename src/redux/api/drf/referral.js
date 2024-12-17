import drfApi from 'redux/api/drf';

const referralApi = drfApi.injectEndpoints({
  endpoints: (builder) => ({
    getReferralCodes: builder.query({
      query: () => ({ url: '/referral/referral-code/' }),
      // You can add providesTags or transformResponse as needed
    }),
    postReferralCode: builder.mutation({
        query: (body) => ({ url: '/referral/referral-code/', method: 'POST', body }),
        invalidatesTags: ['ReferralCode'], // adjust tags as needed
        }),
    deleteReferralCode: builder.mutation({
        query: (id) => ({ url: `/referral/referral-code/${id}/`, method: 'DELETE' }),
        invalidatesTags: ['ReferralCode'], // adjust tags as needed
    }),
    getReferrals: builder.query({
      query: () => ({ url: '/referral/referrals/' }),
    }),
    postReferral: builder.mutation({
      query: (body) => ({ url: '/referral/referrals/', method: 'POST', body }),
      invalidatesTags: ['Refferal'], // adjust tags as needed
    }),
    postAffiliateRequest: builder.mutation({
      query: (body) => ({ url: '/referral/affiliate-request/', method: 'POST', body }),
      invalidatesTags: ['AffiliateRequest'], // adjust tags as needed
    }),
    getSubAffiliates: builder.query({
        query: () => ({ url: '/referral/sub-affiliate/' }),
    }),
    getAffiliateTier: builder.query({
        query: () => ({ url: '/referral/affiliate-tier/' }),
    }),
    getCommissionHistory: builder.query({
      query: () => ({ url: '/referral/commission-history/' }),
  }),
  }),
});

export const {
    useGetReferralCodesQuery,
    useLazyGetReferralCodesQuery,
    usePostReferralCodeMutation,
    useDeleteReferralCodeMutation,
    useGetReferralsQuery,
    useLazyGetReferralsQuery,
    usePostReferralMutation,
    usePostAffiliateRequestMutation,
    useGetSubAffiliatesQuery,
    useLazyGetAffiliatesQuery,
    useGetAffiliateTierQuery,
    useLazyGetAffiliateTierQuery,
    useGetCommissionHistoryQuery,
} = referralApi;

export default referralApi;