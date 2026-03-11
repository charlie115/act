import drfApi from 'redux/api/drf';

const api = drfApi.injectEndpoints({
  endpoints: (builder) => ({
    getWalletAddress: builder.query({
      keepUnusedDataFor: 1,
        query: (userUuid) => ({
            url: `/wallet/address/${userUuid}/`,
        })
      }),
    getWalletBalance: builder.query({
      keepUnusedDataFor: 1,
      query: ({ userUuid, asset }) => ({
        url: `/wallet/balance/${userUuid}/`,
        params: { asset },
      }),
    }),
    postWalletTransaction: builder.mutation({
        query: (body) => ({ url: '/wallet/transaction/', method: 'POST', body }),
        invalidatesTags: ['WalletTransaction'],
      }),
  }),
});

export default api;
export const {
    useGetWalletAddressQuery,
    useLazyGetWalletAddressQuery,
    useGetWalletBalanceQuery,
    useLazyGetWalletBalanceQuery,
    usePostWalletTransactionMutation,
    useLazyPostWalletTransactionMutation,
} = api;
