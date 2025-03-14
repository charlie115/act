import drfApi from 'redux/api/drf';

const FAVORITE_ASSETS_URL = '/users/favorite-assets/';
const UNBIND_TELEGRAM_URL = '/users/users/unbind-telegram/';

const api = drfApi.injectEndpoints({
  endpoints: (builder) => ({
    createFavoriteAsset: builder.mutation({
      query: (args) => ({
        url: FAVORITE_ASSETS_URL,
        method: 'POST',
        body: {
          base_asset: args.baseAsset,
          market_codes: [args.targetMarketCode, args.originMarketCode],
        },
      }),
      invalidatesTags: ['FavoriteAssets'],
    }),
    deleteFavoriteAsset: builder.mutation({
      query: (id) => ({
        url: `${FAVORITE_ASSETS_URL}${id}/`,
        method: 'DELETE',
      }),
      invalidatesTags: ['FavoriteAssets'],
    }),
    getFavoriteAssets: builder.query({
      query: (params) => ({
        url: FAVORITE_ASSETS_URL,
        params,
      }),
      providesTags: ['FavoriteAssets'],
      transformResponse: (response) =>
        response?.results?.reduce(
          (acc, value) => ({ ...acc, [value.base_asset]: value.id }),
          {}
        ),
    }),
    getDepositBalance: builder.query({
      keepUnusedDataFor: 1,
      query: (params) => ({
        url: '/users/deposit-balance/',
        params,
      }),
    }),
    getDepositHistory: builder.query({
      keepUnusedDataFor: 1,
      query: (params) => ({
        url: '/users/deposit-history/',
        params,
      }),
    }),
    getWithdrawalRequests: builder.query({
      keepUnusedDataFor: 1,
      query: (params) => ({
        url: '/users/withdrawal-request/',
        params,
      }),
    }),
    postWithdrawalRequest: builder.mutation({
      query: (args) => ({ 
        url: '/users/withdrawal-request/',
        method: 'POST',
        body: {
          amount: args.amount,
          type: args.type,
          address: args.address,
        },
     }),
      invalidatesTags: ['WithdrawalRequests'],
    }),
    unbindTelegram: builder.mutation({
      query: () => ({
        url: UNBIND_TELEGRAM_URL,
        method: 'POST',
      }),
      invalidatesTags: ['User'],
    }),
  }),
});

export default api;
export const {
  useCreateFavoriteAssetMutation,
  useDeleteFavoriteAssetMutation,
  useGetFavoriteAssetsQuery,
  useGetDepositBalanceQuery,
  useGetDepositHistoryQuery,
  useLazyGetDepositBalanceQuery,
  useGetWithdrawalRequestsQuery,
  usePostWithdrawalRequestMutation,
  useUnbindTelegramMutation,
} = api;
