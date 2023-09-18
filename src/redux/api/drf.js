import { createApi } from '@reduxjs/toolkit/query/react';

import baseQueryWithReAuth from './baseQueryWithReAuth';

const api = createApi({
  reducerPath: 'api',
  baseQuery: baseQueryWithReAuth,
  endpoints: (builder) => ({
    authLogin: builder.mutation({
      query: (body) => ({
        url: '/auth/login/',
        method: 'POST',
        body,
      }),
    }),
    authUserRegister: builder.mutation({
      query: (body) => ({
        url: '/auth/user/register/',
        method: 'PATCH',
        body,
      }),
    }),
  }),
});

export default api;
export const { useAuthLoginMutation, useAuthUserRegisterMutation } = api;
