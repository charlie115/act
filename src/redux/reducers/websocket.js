import { createSlice } from '@reduxjs/toolkit';

export const websocketSlice = createSlice({
  name: 'websocket',
  initialState: {
    coins: [],
  },
  reducers: {
    storeCoins: (state, { payload }) => {
      state.coins = payload;
    },
  },
  // extraReducers: () => {
  // },
});

export const { storeCoins } = websocketSlice.actions;
export default websocketSlice.reducer;
