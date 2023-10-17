import drfApi from 'redux/api/drf';

import { DateTime } from 'luxon';

const api = drfApi.injectEndpoints({
  endpoints: (builder) => ({
    getPastMessages: builder.query({
      query: (params) => ({
        url: '/chat/past/',
        params,
      }),
      transformResponse: (response) =>
        response?.map((item, idx) => ({
          ...item,
          id: `past-${idx}-${DateTime.now().toMillis()}`,
        })),
    }),
    getRandomUsername: builder.query({
      query: () => '/chat/username/',
    }),
  }),
});

export default api;
export const { useGetPastMessagesQuery, useGetRandomUsernameQuery } = api;
