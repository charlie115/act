import drfApi from 'redux/api/drf';

const USER_FEELEVEL_URL = '/fee/user-feelevel/';

const api = drfApi.injectEndpoints({
  endpoints: (builder) => ({
    getUserFeeLevel: builder.query({
      query: () => ({
        url: USER_FEELEVEL_URL,
        method: 'GET',
      }),
      transformResponse: (response) => response,
    }),
  }),
});

export default api;
export const { useGetUserFeeLevelQuery } = api; 