import drfApi from 'redux/api/drf';

const FAVORITE_ASSETS_URL = '/users/favorite-assets/';

const api = drfApi.injectEndpoints({
  endpoints: (builder) => ({
    createFavoriteAssets: builder.mutation({
      query: (args) => ({
        url: FAVORITE_ASSETS_URL,
        method: 'POST',
        body: {
          base_asset: args.baseAsset,
          market_codes: [args.targetMarketCode, args.originMarketCode],
        },
      }),
      invalidatesTags: ['FavoriteAssets'],
    }),
    deleteFavoriteAssets: builder.mutation({
      query: (id) => ({
        url: `${FAVORITE_ASSETS_URL}${id}/`,
        method: 'DELETE',
      }),
      invalidatesTags: ['FavoriteAssets'],
    }),
    getFavoriteAssets: builder.query({
      query: (args) => ({
        url: FAVORITE_ASSETS_URL,
        params: {
          market_codes: `${args.targetMarketCode},${args.originMarketCode}`,
        },
      }),
      providesTags: ['FavoriteAssets'],
      transformResponse: (response) =>
        response?.results?.reduce(
          (acc, value) => ({ ...acc, [value.base_asset]: value.id }),
          {}
        ),
    }),
  }),
});

export default api;
export const {
  useCreateFavoriteAssetsMutation,
  useDeleteFavoriteAssetsMutation,
  useGetFavoriteAssetsQuery,
} = api;
