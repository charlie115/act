import drfApi from 'redux/api/drf';

const api = drfApi.injectEndpoints({
  endpoints: (builder) => ({
    getHistoricalKline: builder.query({
      query: (params) => ({
        url: '/infocore/kline/',
        params,
      }),
      transformResponse: (response) => response?.results,
    }),
  }),
});

export default api;
export const { useGetHistoricalKlineQuery } = api;
