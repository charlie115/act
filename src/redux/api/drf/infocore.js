import drfApi from 'redux/api/drf';

import baseQueryWithReAuth from 'utils/baseQueryWithReAuth';

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
    getFundingRateByMarketCode: builder.query({
      keepUnusedDataFor: 1,
      providesTags: ['FundingRateByMarketCode'],
      queryFn: async ({ assetsByMarketCode }, queryApi, extraOptions) => {
        try {
          const promises = Object.keys(assetsByMarketCode).map((marketCode) =>
            baseQueryWithReAuth(
              {
                url: '/infocore/funding-rate/',
                params: {
                  marketCode,
                  baseAsset: Object.keys(assetsByMarketCode[marketCode]).join(),
                },
              },
              queryApi,
              extraOptions
            )
          );
          const results = await Promise.allSettled(promises);
          const okResults = results.filter(
            (result) => result.value.meta.response.ok
          );
          const data = okResults.reduce((acc, result) => {
            const url = new URL(result.value.meta.request?.url);
            const marketCode = url.searchParams.get('market_code');
            acc[marketCode] = result.value.data;
            return acc;
          }, {});
          const meta = okResults.reduce((acc, result) => {
            const url = new URL(result.value.meta.request?.url);
            const marketCode = url.searchParams.get('market_code');
            acc[marketCode] = result.value.meta;
            return acc;
          }, []);
          return { data, meta };
        } catch (error) {
          // Catch any errors and return them as an object with an `error` field
          return { error };
        }
      },
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
  useGetFundingRateByMarketCodeQuery,
  useGetFundingRateDiffQuery,
  useGetHistoricalKlineQuery,
  useGetMarketCodesQuery,
  useGetWalletStatusQuery,
  useLazyGetFundingRateQuery,
  usePostAssetMutation,
} = api;
