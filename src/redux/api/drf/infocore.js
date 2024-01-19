import drfApi from 'redux/api/drf';

import { DateTime } from 'luxon';

import { DATE_FORMAT_API_QUERY } from 'constants';
import { INTERVAL_LIST } from 'constants/lists';

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
      transformResponse: (response, _, params) => {
        const transformedResponse = [];
        const interval = INTERVAL_LIST.find(
          (item) => params.interval === item.value
        );
        response.forEach((item, index) => {
          transformedResponse.push(item);
          if (response[index + 1]) {
            const dateTimeNow = DateTime.fromISO(item.datetime_now);
            const dateTimeNext = DateTime.fromISO(
              response[index + 1].datetime_now
            );
            const diff = dateTimeNext
              .diff(dateTimeNow, [interval.unit])
              .toObject();

            if (diff[interval.unit] > interval.quantity) {
              Array.from(
                {
                  length:
                    diff[interval.unit] / interval.quantity - interval.quantity,
                },
                (_1, i) => i + 1
              ).forEach((num) => {
                const time = dateTimeNow.plus({
                  [interval.unit]: num * interval.quantity,
                });
                transformedResponse.push({
                  datetime_now: time.toString(),
                });
              });
            }
          }
        });
        return transformedResponse;
      },
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
  useGetFundingRateQuery,
  useGetFundingRateDiffQuery,
  useGetHistoricalKlineQuery,
  useGetMarketCodesQuery,
  useGetWalletStatusQuery,
  usePostAssetMutation,
} = api;
