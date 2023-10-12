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
    logout: builder.mutation({
      query: () => ({
        url: '/auth/logout/',
        method: 'POST',
      }),
    }),
    userRegister: builder.mutation({
      query: (body) => ({
        url: '/auth/user/register/',
        method: 'PATCH',
        body,
      }),
    }),
    user: builder.query({ query: () => '/auth/user/' }),
  }),
});

export default api;
export const {
  useLoginMutation,
  useLogoutMutation,
  useUserRegisterMutation,
  useUserQuery,
} = api;
