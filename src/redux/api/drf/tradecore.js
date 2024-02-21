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
    getTradeConfig: builder.query({
      providesTags: ['TradeConfig'],
      keepUnusedDataFor: 1,
      query: ({ uuid, ...params }) => ({
        url: `/tradecore/trade-config/${uuid}/`,
        params,
      }),
    }),
    deleteMultipleTrades: builder.mutation({
      queryFn: async (items, queryApi, extraOptions) => {
        try {
          const promises = items.map((item) =>
            baseQueryWithReAuth(
              {
                url: `/tradecore/trades/${item.uuid}/`,
                method: 'DELETE',
                params: item.params,
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
      invalidatesTags: ['AllTrades', 'TradesByTradeConfig'],
    }),
    getAllTrades: builder.query({
      keepUnusedDataFor: 1,
      providesTags: ['AllTrades'],
      queryFn: async ({ tradeConfigUuids, params }, queryApi, extraOptions) => {
        try {
          const promises = tradeConfigUuids.map((tradeConfigUuid) =>
            baseQueryWithReAuth(
              {
                url: '/tradecore/trades/',
                params: { tradeConfigUuid, ...params },
              },
              queryApi,
              extraOptions
            )
          );
          const results = await Promise.allSettled(promises);
          const data = results.reduce(
            (acc, result) => acc.concat(result.value.data),
            []
          );
          const meta = results.reduce(
            (acc, result) => acc.concat(result.value.meta),
            []
          );
          return { data, meta };
        } catch (error) {
          // Catch any errors and return them as an object with an `error` field
          return { error };
        }
      },
    }),
    getTradesByTradeConfig: builder.query({
      keepUnusedDataFor: 1,
      providesTags: ['TradesByTradeConfig'],
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
      invalidatesTags: ['TradesByTradeConfig'],
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
      invalidatesTags: ['AllTrades', 'TradesByTradeConfig'],
    }),
    putTradeConfig: builder.mutation({
      query: ({ uuid, ...body }) => ({
        url: `/tradecore/trade-config/${uuid}/`,
        method: 'PUT',
        // params: { tradeConfigUuid: body.trade_config_uuid },
        body,
      }),
      invalidatesTags: ['TradeConfig'],
    }),
  }),
});

export default api;
export const {
  useDeleteMultipleTradesMutation,
  useGetAllTradesQuery,
  useGetNodesQuery,
  useGetTradeConfigQuery,
  useGetTradesByTradeConfigQuery,
  usePostTradeMutation,
  usePostTradeConfigMutation,
  usePutTradeMutation,
  usePutTradeConfigMutation,
} = api;
