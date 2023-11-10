import drfApi from 'redux/api/drf';

const api = drfApi.injectEndpoints({
  endpoints: (builder) => ({
    getAssets: builder.query({
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
      query: (params) => ({
        url: '/infocore/funding-rate/',
        params,
      }),
      transformResponse: (response) =>
        response?.reduce(
          (acc, value) => ({
            ...acc,
            [value.base_asset]: { ...value },
          }),
          {}
        ),
    }),
    getHistoricalKline: builder.query({
      query: (params) => ({
        url: '/infocore/kline/',
        params,
      }),
    }),
    getMarketCodes: builder.query({
      keepUnusedDataFor: 5,
      query: () => '/infocore/market-codes/',
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
  usePostAssetMutation,
} = api;
