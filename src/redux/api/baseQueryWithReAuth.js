import { fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import { Mutex } from 'async-mutex';

// create a new mutex
const mutex = new Mutex();

export const baseQuery = fetchBaseQuery({
  baseUrl: process.env.REACT_APP_DRF_URL,
  prepareHeaders: (headers, { getState }) => {
    const { accessToken } = getState().auth;
    if (accessToken) headers.set('Authorization', `Bearer ${accessToken}`);

    return headers;
  },
});

export default async (args, api, extraOptions) => {
  // wait until the mutex is available without locking it
  await mutex.waitForUnlock();
  let result = await baseQuery(args, api, extraOptions);
  if (result.error && result.error.status === 401) {
    // checking whether the mutex is locked
    if (!mutex.isLocked()) {
      const release = await mutex.acquire();
      try {
        const { refreshToken: refresh } = api.getState().auth;
        const refreshResult = await baseQuery(
          { url: '/auth/token/refresh/', method: 'POST', body: { refresh } },
          api,
          extraOptions
        );
        if (refreshResult.data) {
          api.dispatch({
            type: 'auth/newTokenReceived',
            payload: refreshResult.data,
          });
          // retry the initial query
          result = await baseQuery(args, api, extraOptions);
        } else {
          await baseQuery(
            { url: '/auth/logout/', method: 'POST' },
            api,
            extraOptions
          );
          api.dispatch({ type: 'auth/logout' });
        }
      } finally {
        // release must be called once the mutex should be released again.
        release();
      }
    } else {
      // wait until the mutex is available without locking it
      await mutex.waitForUnlock();
      result = await baseQuery(args, api, extraOptions);
    }
  }
  return result;
};
