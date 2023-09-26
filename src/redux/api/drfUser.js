import drfApi from 'redux/api/drf';

// const FAVORITE_ASSETS_URL = '/users/favorite-assets/';
const FAVORITE_ASSETS_URL = '/users/favorite-symbols/'; // TODO: Remove once final API is deployed

const api = drfApi.injectEndpoints({
  endpoints: (builder) => ({
    createFavoriteAssets: builder.mutation({
      query: (args) => ({
        url: FAVORITE_ASSETS_URL,
        method: 'POST',
        body: {
          base_asset: args.baseAsset,
          market_codes: [args.targetMarketCode, args.originMarketCode],

          // TODO: Remove once final API is deployed
          base_symbol: args.baseAsset,
          market_name_1: args.targetMarketCode,
          market_name_2: args.originMarketCode,
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
          market_codes: [args.targetMarketCode, args.originMarketCode],

          // TODO: Remove once final API is deployed
          market_name_1: args.targetMarketCode,
          market_name_2: args.originMarketCode,
        },
      }),
      providesTags: ['FavoriteAssets'],
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
  useCreateFavoriteAssetsMutation,
  useDeleteFavoriteAssetsMutation,
  useGetFavoriteAssetsQuery,
} = api;
