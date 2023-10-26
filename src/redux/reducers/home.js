import { createSlice } from '@reduxjs/toolkit';

import drfAuthApi from 'redux/api/drf/auth';

const initialState = {
  bookmarkedMarketCodePairs: { selected: null, list: [] },
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
    selectBookmarkMarketCodePair: (state, { payload }) => {
      state.bookmarkedMarketCodePairs.selected = payload;
    },
    toggleBookmarkMarketCodePair: (state, { payload }) => {
      const { selected, list } = state.bookmarkedMarketCodePairs;
      let newSelected = null;
      let newList = list || [];

      const selectedPair = list?.find(
        (pair) => pair[0] === payload[0] && pair[1] === payload[1]
      );
      if (selectedPair) {
        newList = list?.filter(
          (item) => !(item[0] === payload[0] && item[1] === payload[1])
        );
        if (
          selectedPair[0] === selected?.[0] &&
          selectedPair[1] === selected?.[1]
        )
          newSelected = null;
      } else {
        newList.push(payload);
        newSelected = payload;
      }
      state.bookmarkedMarketCodePairs = {
        selected: newSelected,
        list: newList,
      };
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
  selectBookmarkMarketCodePair,
  toggleBookmarkMarketCodePair,
  togglePriceView,
} = homeSlice.actions;

export default homeSlice.reducer;
