import { createSlice } from '@reduxjs/toolkit';

import drfAuthApi from 'redux/api/drfAuth';

const initialState = { favoriteAssets: {} };

export const homeSlice = createSlice({
  name: 'home',
  initialState,
  reducers: {
    addLocalFavoriteAsset: (state, { payload }) => {
      if (!state.favoriteAssets[payload.marketKey])
        state.favoriteAssets[payload.marketKey] = [];
      state.favoriteAssets[payload.marketKey].push(payload.baseAsset);
    },
    removeLocalFavoriteAsset: (state, { payload }) => {
      state.favoriteAssets?.[payload.marketKey]?.splice(payload.id, 1);
    },
  },
  extraReducers: (builder) => {
    builder.addMatcher(drfAuthApi.endpoints.login.matchFulfilled, (state) => {
      state.favoriteAssets = {};
    });
  },
});

export const { addLocalFavoriteAsset, removeLocalFavoriteAsset } =
  homeSlice.actions;

export default homeSlice.reducer;
