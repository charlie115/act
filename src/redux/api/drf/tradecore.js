import drfApi from 'redux/api/drf';

import baseQueryWithReAuth from 'utils/baseQueryWithReAuth';

const api = drfApi.injectEndpoints({
  endpoints: (builder) => ({
    getNodes: builder.query({
      keepUnusedDataFor: 1,
      query: (params) => ({
        url: '/tradecore/nodes/',
        params,
      }),
    }),
    deleteMultipleTrades: builder.mutation({
      queryFn: async ({ uuids, params }, queryApi, extraOptions) => {
        try {
          const promises = uuids.map((id) =>
            baseQueryWithReAuth(
              {
                url: `/tradecore/trades/${id}`,
                method: 'DELETE',
                params,
              },
              queryApi,
              extraOptions
            )
          );
          const results = await Promise.allSettled(promises);
          return {
            data: results.map((result) => result.value.data),
            meta: results.map((result) => result.value.meta),
          };
        } catch (error) {
          // Catch any errors and return them as an object with an `error` field
          return { error };
        }
      },
      invalidatesTags: ['Trades'],
    }),
    getTrades: builder.query({
      keepUnusedDataFor: 1,
      providesTags: ['Trades'],
      query: (params) => ({
        url: '/tradecore/trades/',
        params,
      }),
    }),
    postTrade: builder.mutation({
      query: (body) => ({
        url: '/tradecore/trades/',
        method: 'POST',
        body,
      }),
      invalidatesTags: ['Trades'],
    }),
    postTradeConfig: builder.mutation({
      query: (body) => ({
        url: '/tradecore/trade-config/',
        method: 'POST',
        body,
      }),
      invalidatesTags: ['User'],
    }),
    putTrade: builder.mutation({
      query: ({ uuid, ...body }) => ({
        url: `/tradecore/trades/${uuid}/`,
        method: 'PUT',
        params: { tradeConfigUuid: body.trade_config_uuid },
        body,
      }),
      invalidatesTags: ['Trades'],
    }),
  }),
});

export default api;
export const {
  useDeleteMultipleTradesMutation,
  useGetNodesQuery,
  useGetTradesQuery,
  usePostTradeMutation,
  usePostTradeConfigMutation,
  usePutTradeMutation,
} = api;
