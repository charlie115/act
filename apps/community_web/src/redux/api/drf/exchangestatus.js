import drfApi from 'redux/api/drf';

const exchangeStatusApi = drfApi.injectEndpoints({
  endpoints: (builder) => ({
    getExchangeStatuses: builder.query({
      query: () => ({ url: '/exchange-status/server-status/' }),
    }),
  }),
});

export const {
  useGetExchangeStatusesQuery,
} = exchangeStatusApi;

export default exchangeStatusApi;