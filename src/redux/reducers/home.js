import { createSlice } from '@reduxjs/toolkit';

import drfApi from 'redux/api/drf';

const initialState = { favoriteSymbols: {} };

export const homeSlice = createSlice({
  name: 'home',
  initialState,
  reducers: {
    addLocalFavoriteSymbol: (state, { payload }) => {
      if (!state.favoriteSymbols[payload.marketExchangeKey])
        state.favoriteSymbols[payload.marketExchangeKey] = [];
      state.favoriteSymbols[payload.marketExchangeKey].push(payload.symbol);
    },
    removeLocalFavoriteSymbol: (state, { payload }) => {
      state.favoriteSymbols?.[payload.marketExchangeKey]?.splice(payload.id, 1);
    },
  },
  extraReducers: (builder) => {
    builder.addMatcher(drfApi.endpoints.authLogin.matchFulfilled, (state) => {
      state.favoriteSymbols = {};
    });
  },
});

export const { addLocalFavoriteSymbol, removeLocalFavoriteSymbol } =
  homeSlice.actions;

export default homeSlice.reducer;
