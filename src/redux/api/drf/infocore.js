import drfApi from 'redux/api/drf';

const api = drfApi.injectEndpoints({
  endpoints: (builder) => ({
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
      transformResponse: (response) => response,
    }),
  }),
});

export default api;
export const { useGetFundingRateQuery, useGetHistoricalKlineQuery } = api;
