import drfApi from 'redux/api/drf';

const api = drfApi.injectEndpoints({
  endpoints: (builder) => ({
    getWalletAddress: builder.query({
      keepUnusedDataFor: 1,
        // query: (params) => ({
        //   url: '/wallet/address/',
        //   params,
        // }),
        query: (userUuid) => ({
            url: `/wallet/address/${userUuid}/`,
        })
      }),
    getWalletBalance: builder.query({
      keepUnusedDataFor: 1,
      query: (params) => ({
        url: '/wallet/balance/',
        params,
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
