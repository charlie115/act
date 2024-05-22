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
    deleteRepeatTrade: builder.mutation({
      query: ({ id, ...params }) => ({
        url: `/tradecore/repeat-trades/${id}/`,
        method: 'DELETE',
        params,
      }),
      invalidatesTags: ['AllRepeatTrades', 'RepeatTradesByTradeConfig'],
    }),
    getAllRepeatTrades: builder.query({
      keepUnusedDataFor: 1,
      providesTags: ['AllRepeatTrades', 'RepeatTradesByTradeConfig'],
      queryFn: async ({ tradeConfigUuids, params }, queryApi, extraOptions) => {
        try {
          const promises = tradeConfigUuids.map((tradeConfigUuid) =>
            baseQueryWithReAuth(
              {
                url: '/tradecore/repeat-trades/',
                params: { tradeConfigUuid, ...params },
              },
              queryApi,
              extraOptions
            )
          );
          const results = await Promise.allSettled(promises);
          const okResults = results.filter(
            (result) => result.value.meta.response.ok
          );
          const data = okResults.reduce(
            (acc, result) =>
              acc.concat(result.value.data || result.value.error),
            []
          );
          const meta = okResults.reduce(
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
          const okResults = results.filter(
            (result) => result.value.meta.response.ok
          );

          const data = okResults.reduce(
            (acc, result) => acc.concat(result.value.data),
            []
          );
          const meta = okResults.reduce(
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
    getDepositAddress: builder.query({
      keepUnusedDataFor: 1,
      query: (params) => ({
        url: '/tradecore/deposit-address/',
        params,
      }),
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
    getOrderHistoryByUuid: builder.query({
      keepUnusedDataFor: 1,
      query: ({ uuid, ...params }) => ({
        url: `/tradecore/order-history/${uuid}/`,
        params,
      }),
    }),
    getPBoundary: builder.query({
      keepUnusedDataFor: 1,
      query: (params) => ({
        url: '/tradecore/pboundary/',
        params,
      }),
    }),
    getPnlHistory: builder.query({
      keepUnusedDataFor: 1,
      query: (params) => ({
        url: '/tradecore/pnl-history/',
        params,
      }),
    }),
    getRepeatTradesByTradeConfig: builder.query({
      keepUnusedDataFor: 1,
      providesTags: ['RepeatTradesByTradeConfig'],
      query: (params) => ({
        url: '/tradecore/repeat-trades/',
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
    getTradeByUuid: builder.query({
      keepUnusedDataFor: 1,
      query: ({ uuid, ...params }) => ({
        url: `/tradecore/trades/${uuid}/`,
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
    getTradeHistory: builder.query({
      keepUnusedDataFor: 1,
      query: (params) => ({
        url: '/tradecore/trade-history/',
        params,
      }),
    }),
    getTradeHistoryByUuid: builder.query({
      keepUnusedDataFor: 1,
      query: ({ uuid, ...params }) => ({
        url: `/tradecore/trade-history/${uuid}/`,
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
    postDepositAmount: builder.mutation({
      query: (body) => ({
        url: '/tradecore/deposit-amount/',
        method: 'POST',
        body,
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
    postRepeatTrade: builder.mutation({
      query: (body) => ({
        url: '/tradecore/repeat-trades/',
        method: 'POST',
        body,
      }),
      invalidatesTags: ['AllRepeatTrades', 'RepeatTradesByTradeConfig'],
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
    putRepeatTrade: builder.mutation({
      query: ({ uuid, ...body }) => ({
        url: `/tradecore/repeat-trades/${uuid}/`,
        method: 'PUT',
        params: { tradeConfigUuid: body.trade_config_uuid },
        body,
      }),
      invalidatesTags: ['AllRepeatTrades', 'RepeatTradesByTradeConfig'],
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
  useDeleteRepeatTradeMutation,
  useGetAllRepeatTradesQuery,
  useGetAllTradesQuery,
  useGetDepositAddressQuery,
  useGetExchangeApiKeyQuery,
  useGetFuturesPositionQuery,
  useGetNodesQuery,
  useGetOrderHistoryByUuidQuery,
  useGetPBoundaryQuery,
  useGetPnlHistoryQuery,
  useGetRepeatTradesByTradeConfigQuery,
  useGetSpotPositionQuery,
  useGetTradeByUuidQuery,
  useGetTradeConfigQuery,
  useGetTradeHistoryQuery,
  useGetTradeHistoryByUuidQuery,
  useGetTradesByTradeConfigQuery,
  useLazyGetPnlHistoryQuery,
  useLazyGetPBoundaryQuery,
  useLazyGetRepeatTradesByTradeConfigQuery,
  useLazyGetTradeConfigQuery,
  usePostDepositAmountMutation,
  usePostExchangeApiKeyMutation,
  usePostRepeatTradeMutation,
  usePostTradeMutation,
  usePostTradeConfigMutation,
  usePutRepeatTradeMutation,
  usePutTradeMutation,
  usePutTradeConfigMutation,
} = api;
