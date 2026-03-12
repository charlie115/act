import drfApi from 'redux/api/drf';

import baseQueryWithReAuth from 'utils/baseQueryWithReAuth';

const api = drfApi.injectEndpoints({
  endpoints: (builder) => ({
    getMessages: builder.query({
      keepUnusedDataFor: 1,
      providesTags: ['TelegramMessages'],
      query: (params) => ({
        url: '/messagecore/messages/',
        params,
      }),
    }),
    patchMessage: builder.mutation({
      query: ({ id, ...body }) => ({
        url: `/messagecore/messages/${id}/`,
        method: 'PATCH',
        body,
      }),
      invalidatesTags: ['TelegramMessages'],
    }),
    patchMultipleMessages: builder.mutation({
      queryFn: async (items, queryApi, extraOptions) => {
        try {
          const promises = items.map((item) =>
            baseQueryWithReAuth(
              {
                url: `/messagecore/messages/${item.id}/`,
                method: 'PATCH',
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
      invalidatesTags: ['TelegramMessages'],
    }),
  }),
});

export default api;
export const {
  useGetMessagesQuery,
  usePatchMessageMutation,
  usePatchMultipleMessagesMutation,
} = api;
