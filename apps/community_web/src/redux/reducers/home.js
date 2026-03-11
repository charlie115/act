import { createSlice } from '@reduxjs/toolkit';

import drfAuthApi from 'redux/api/drf/auth';

const initialState = {
  bookmarkedMarketCodes: {},
  defaultMarketCodes: {},
  favoriteAssets: {},
  priceView: 'kimp',
};

export const homeSlice = createSlice({
  name: 'home',
  initialState,
  reducers: {
    addLocalFavoriteAsset: (state, { payload }) => {
      if (!state.favoriteAssets[payload.marketCodeKey])
        state.favoriteAssets[payload.marketCodeKey] = [];
      state.favoriteAssets[payload.marketCodeKey].push(payload.baseAsset);
    },
    changeDefaultMarketCodes: (state, { payload }) => {
      state.defaultMarketCodes = payload;
    },
    removeLocalFavoriteAsset: (state, { payload }) => {
      state.favoriteAssets?.[payload.marketCodeKey]?.splice(payload.id, 1);
    },
    selectBookmarkMarketCodes: (state, { payload }) => {
      state.defaultMarketCodes = payload;
    },
    toggleBookmarkMarketCodes: (state, { payload }) => {
      if (!state.bookmarkedMarketCodes[payload.target])
        state.bookmarkedMarketCodes[payload.target] = {};
      state.bookmarkedMarketCodes[payload.target][payload.origin] =
        !state.bookmarkedMarketCodes[payload.target][payload.origin];
    },
    togglePriceView: (state, { payload }) => {
      state.priceView = payload;
    },
  },
  extraReducers: (builder) => {
    builder.addMatcher(drfAuthApi.endpoints.login.matchFulfilled, (state) => {
      state.favoriteAssets = {};
    });
  },
});

export const {
  addLocalFavoriteAsset,
  changeDefaultMarketCodes,
  removeLocalFavoriteAsset,
  selectBookmarkMarketCodePair,
  toggleBookmarkMarketCodePair,
  selectBookmarkMarketCodes,
  toggleBookmarkMarketCodes,
  togglePriceView,
} = homeSlice.actions;

export default homeSlice.reducer;
