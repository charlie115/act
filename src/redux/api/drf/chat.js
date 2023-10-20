import drfApi from 'redux/api/drf';

import { DateTime } from 'luxon';

import sortBy from 'lodash/sortBy';

const api = drfApi.injectEndpoints({
  endpoints: (builder) => ({
    getPastMessages: builder.query({
      query: (params) => ({
        url: '/chat/past/',
        params,
      }),
      transformResponse: (response) =>
        sortBy(response?.results || [], 'datetime')?.map((item, idx) => ({
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
