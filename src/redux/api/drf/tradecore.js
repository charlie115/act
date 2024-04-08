import drfApi from 'redux/api/drf';

import baseQueryWithReAuth from 'utils/baseQueryWithReAuth';

const api = drfApi.injectEndpoints({
  endpoints: (builder) => ({
    deleteExchangeApiKey: builder.mutation({
      query: ({ id, ...params }) => ({
        url: `/tradecore/exchange-api-key/${id}/`,
        method: 'DELETE',
        params,
      }),
      invalidatesTags: ['ExchangeApiKey'],
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
    getExchangeApiKey: builder.query({
      keepUnusedDataFor: 1,
      providesTags: ['ExchangeApiKey'],
      query: (params) => ({
        url: '/tradecore/exchange-api-key/',
        params,
      }),
    }),
    getFuturesPosition: builder.query({
      keepUnusedDataFor: 1,
      query: (params) => ({
        url: '/tradecore/futures-position/',
        params,
      }),
    }),
    getNodes: builder.query({
      keepUnusedDataFor: 1,
      query: (params) => ({
        url: '/tradecore/nodes/',
        params,
      }),
    }),
    getSpotPosition: builder.query({
      keepUnusedDataFor: 1,
      query: (params) => ({
        url: '/tradecore/spot-position/',
        params,
      }),
    }),
    getTradeConfig: builder.query({
      keepUnusedDataFor: 1,
      providesTags: ['TradeConfig'],
      query: ({ uuid, ...params }) => ({
        url: `/tradecore/trade-config/${uuid}/`,
        params,
      }),
    }),
    getTradesByTradeConfig: builder.query({
      keepUnusedDataFor: 1,
      providesTags: ['TradesByTradeConfig'],
      query: (params) => ({
        url: '/tradecore/trades/',
        params,
      }),
    }),
    postExchangeApiKey: builder.mutation({
      query: (body) => ({
        url: '/tradecore/exchange-api-key/',
        method: 'POST',
        body,
      }),
      invalidatesTags: ['ExchangeApiKey'],
    }),
    postTrade: builder.mutation({
      query: (body) => ({
        url: '/tradecore/trades/',
        method: 'POST',
        body,
      }),
      invalidatesTags: ['AllTrades', 'TradesByTradeConfig'],
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
  useDeleteExchangeApiKeyMutation,
  useDeleteMultipleTradesMutation,
  useGetAllTradesQuery,
  useGetExchangeApiKeyQuery,
  useGetFuturesPositionQuery,
  useGetNodesQuery,
  useGetSpotPositionQuery,
  useGetTradeConfigQuery,
  useGetTradesByTradeConfigQuery,
  useLazyGetTradeConfigQuery,
  usePostExchangeApiKeyMutation,
  usePostTradeMutation,
  usePostTradeConfigMutation,
  usePutTradeMutation,
  usePutTradeConfigMutation,
} = api;
