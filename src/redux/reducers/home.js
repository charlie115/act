import { createSlice } from '@reduxjs/toolkit';

import drfAuthApi from 'redux/api/drfAuth';

const initialState = { favoriteAssets: {}, priceView: 'kimp' };

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
  togglePriceView,
} = homeSlice.actions;

export default homeSlice.reducer;
