import { createSlice } from '@reduxjs/toolkit';

export const websocketSlice = createSlice({
  name: 'websocket',
  initialState: {
    coins: [],
  },
  reducers: {
    storeCoins: (state, { payload }) => {
      console.log('payload: ', payload);
    },
  },
  // extraReducers: () => {
  // },
});

export const { storeCoins } = websocketSlice.actions;
export default websocketSlice.reducer;
