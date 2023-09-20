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
    authLogout: builder.mutation({
      query: () => ({
        url: '/auth/logout/',
        method: 'POST',
      }),
    }),
    authUserRegister: builder.mutation({
      query: (body) => ({
        url: '/auth/user/register/',
        method: 'PATCH',
        body,
      }),
    }),
    getUsersFavoriteSymbols: builder.query({
      query: (params) => ({
        url: '/users/favorite-symbols/',
        params,
      }),
      providesTags: ['FavoriteSymbols'],
    }),
    usersFavoriteSymbols: builder.mutation({
      query: ({ method, body }) => ({
        url: '/users/favorite-symbols/',
        method,
        body,
      }),
      invalidatesTags: ['FavoriteSymbols'],
    }),
  }),
});

export default api;
export const {
  useAuthLoginMutation,
  useAuthLogoutMutation,
  useAuthUserRegisterMutation,
  useUsersFavoriteSymbolsMutation,
  useGetUsersFavoriteSymbolsQuery,
} = api;
