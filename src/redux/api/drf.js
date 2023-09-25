import { createApi } from '@reduxjs/toolkit/query/react';

import baseQueryWithReAuth from './baseQueryWithReAuth';

const api = createApi({
  reducerPath: 'api',
  baseQuery: baseQueryWithReAuth,
  endpoints: (builder) => ({
    // MUTATIONS
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
    createUsersFavoriteSymbols: builder.mutation({
      query: (body) => ({
        url: '/users/favorite-symbols/',
        method: 'POST',
        body,
      }),
      invalidatesTags: ['FavoriteSymbols'],
    }),
    deleteUsersFavoriteSymbols: builder.mutation({
      query: (id) => ({
        url: `/users/favorite-symbols/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['FavoriteSymbols'],
    }),
    // QUERIES
    authUser: builder.query({
      query: () => '/auth/user/',
    }),
    getUsersFavoriteSymbols: builder.query({
      query: (params) => ({
        url: '/users/favorite-symbols/',
        params,
      }),
      providesTags: ['FavoriteSymbols'],
      transformResponse: (response) =>
        response?.results?.reduce(
          (acc, value) => ({ ...acc, [value.base_symbol]: value.id }),
          {}
        ),
    }),
  }),
});

export default api;
export const {
  useAuthLoginMutation,
  useAuthLogoutMutation,
  useAuthUserRegisterMutation,
  useCreateUsersFavoriteSymbolsMutation,
  useDeleteUsersFavoriteSymbolsMutation,
  useAuthUserQuery,
  useGetUsersFavoriteSymbolsQuery,
} = api;
