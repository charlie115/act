import drfApi from 'redux/api/drf';

const api = drfApi.injectEndpoints({
  endpoints: (builder) => ({
    login: builder.mutation({
      query: (body) => ({
        url: '/auth/login/',
        method: 'POST',
        body,
      }),
    }),
    loginTelegram: builder.mutation({
      invalidatesTags: ['User'],
      query: (body) => ({
        url: '/auth/login/telegram/',
        method: 'POST',
        body,
      }),
    }),
    logout: builder.mutation({
      query: () => ({
        url: '/auth/logout/',
        method: 'POST',
      }),
    }),
    userPatch: builder.mutation({
      query: (body) => ({
        url: '/auth/user/',
        method: 'PATCH',
        body,
      }),
    }),
    userRegister: builder.mutation({
      query: (body) => ({
        url: '/auth/user/register/',
        method: 'PATCH',
        body,
      }),
    }),
    user: builder.query({ query: () => '/auth/user/', providesTags: ['User'] }),
  }),
});

export default api;
export const {
  useLoginMutation,
  useLoginTelegramMutation,
  useLogoutMutation,
  useUserPatchMutation,
  useUserRegisterMutation,
  useUserQuery,
} = api;
