import drfApi from 'redux/api/drf';

const api = drfApi.injectEndpoints({
  endpoints: (builder) => ({
    getAssets: builder.query({
      keepUnusedDataFor: 5,
      query: (params) => ({
        url: '/infocore/assets/',
        params,
      }),
      providesTags: ['Assets'],
      transformResponse: (response) =>
        response?.results?.reduce(
          (acc, value) => ({
            ...acc,
            [value.symbol]: { ...value },
          }),
          {}
        ),
    }),
    getFundingRate: builder.query({
      keepUnusedDataFor: 1,
      query: (params) => ({
        url: '/infocore/funding-rate/',
        params,
      }),
    }),
    getHistoricalKline: builder.query({
      keepUnusedDataFor: 5,
      query: (params) => ({
        url: '/infocore/kline/',
        params,
      }),
    }),
    getMarketCodes: builder.query({
      keepUnusedDataFor: 5,
      query: () => '/infocore/market-codes/',
    }),
    getWalletStatus: builder.query({
      keepUnusedDataFor: 0,
      query: (params) => ({
        url: '/infocore/wallet-status/',
        params,
      }),
    }),
    postAsset: builder.mutation({
      query: (body) => ({
        url: '/infocore/assets/',
        method: 'POST',
        body,
      }),
      invalidatesTags: ['Assets'],
    }),
  }),
});

export default api;
export const {
  useGetAssetsQuery,
  useGetFundingRateQuery,
  useGetHistoricalKlineQuery,
  useGetMarketCodesQuery,
  useGetWalletStatusQuery,
  usePostAssetMutation,
} = api;
