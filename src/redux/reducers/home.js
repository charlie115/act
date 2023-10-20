import { createSlice } from '@reduxjs/toolkit';

import drfAuthApi from 'redux/api/drf/auth';

const initialState = {
  bookmarkedMarketCodePairs: [],
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
    removeLocalFavoriteAsset: (state, { payload }) => {
      state.favoriteAssets?.[payload.marketCodeKey]?.splice(payload.id, 1);
    },
    toggleBookmarkMarketCodePair: (state, { payload }) => {
      const selectedPair = state.bookmarkedMarketCodePairs.find(
        (pair) => pair[0] === payload[0] && pair[1] === payload[1]
      );
      if (selectedPair)
        state.bookmarkedMarketCodePairs =
          state.bookmarkedMarketCodePairs.filter(
            (item) => !(item[0] === payload[0] && item[1] === payload[1])
          );
      else state.bookmarkedMarketCodePairs.push(payload);
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
  removeLocalFavoriteAsset,
  toggleBookmarkMarketCodePair,
  togglePriceView,
} = homeSlice.actions;

export default homeSlice.reducer;
