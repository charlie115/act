import drfApi from 'redux/api/drf';

const api = drfApi.injectEndpoints({
  endpoints: (builder) => ({
    getAssets: builder.query({
      keepUnusedDataFor: 5,
      providesTags: ['Assets'],
      query: (params) => ({
        url: '/infocore/assets/',
        params,
      }),
      transformResponse: (response) =>
        response?.results?.reduce(
          (acc, value) => ({
            ...acc,
            [value.symbol]: { ...value },
          }),
          {}
        ),
    }),
    getAverageFundingRate: builder.query({
      keepUnusedDataFor: 1,
      query: (params) => ({
        url: '/infocore/funding-rate/average/',
        params,
      }),
    }),
    getDollar: builder.query({
      keepUnusedDataFor: 1,
      query: () => ({ url: '/infocore/dollar/' }),
    }),
    getFundingRate: builder.query({
      keepUnusedDataFor: 1,
      query: (params) => ({
        url: '/infocore/funding-rate/',
        params,
      }),
    }),
    getFundingRateDiff: builder.query({
      keepUnusedDataFor: 1,
      query: (params) => ({
        url: '/infocore/funding-rate/diff/',
        params,
      }),
    }),
    getHistoricalKline: builder.query({
      keepUnusedDataFor: 0,
      query: (params) => ({
        url: '/infocore/kline/',
        params,
      }),
    }),
    getMarketCodes: builder.query({
      keepUnusedDataFor: 5,
      query: () => '/infocore/market-codes/',
      // transformResponse: () => ({
      //   'BITHUMB_SPOT/KRW': ['BINANCE_SPOT/USDT', 'OKX_USD_M/USDT'],
      // }),
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
  useGetAverageFundingRateQuery,
  useGetDollarQuery,
  useGetFundingRateQuery,
  useGetFundingRateDiffQuery,
  useGetHistoricalKlineQuery,
  useGetMarketCodesQuery,
  useGetWalletStatusQuery,
  usePostAssetMutation,
} = api;
