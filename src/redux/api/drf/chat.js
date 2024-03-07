import drfApi from 'redux/api/drf';

const api = drfApi.injectEndpoints({
  endpoints: (builder) => ({
    getPastMessages: builder.query({
      query: (params) => ({
        url: '/chat/past/',
        params,
      }),
    }),
    getRandomUsername: builder.query({
      query: () => '/chat/username/',
    }),
  }),
});

export default api;
export const { useGetPastMessagesQuery, useGetRandomUsernameQuery } = api;
