import { fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import { Mutex } from 'async-mutex';

import qs from 'qs';
import snakeCase from 'lodash/snakeCase';

// create a new mutex
const mutex = new Mutex();

export const baseQuery = fetchBaseQuery({
  baseUrl: process.env.REACT_APP_DRF_URL,
  prepareHeaders: (headers, { getState }) => {
    const { id } = getState().auth;
    if (id?.accessToken)
      headers.set('Authorization', `Bearer ${id?.accessToken}`);

    return headers;
  },
  paramsSerializer: (params) => {
    const snakeCasedParams = Object.keys(params).reduce(
      (acc, key) => ({
        ...acc,
        [snakeCase(key)]: params[key],
      }),
      {}
    );
    return qs.stringify(snakeCasedParams, { arrayFormat: 'repeat' });
  },
});

export default async (args, api, extraOptions) => {
  // wait until the mutex is available without locking it
  await mutex.waitForUnlock();
  let result = await baseQuery(args, api, extraOptions);
  if (result.error && result.error.status === 401) {
    if (result.error.data?.code === 'user_not_found') {
      api.dispatch({ type: 'auth/logout' });
      return result;
    }

    // checking whether the mutex is locked
    if (!mutex.isLocked()) {
      const release = await mutex.acquire();
      try {
        const { id } = api.getState().auth;
        const refresh = id?.refreshToken;
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
