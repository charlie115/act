import { createSlice } from '@reduxjs/toolkit';

export const websocketSlice = createSlice({
  name: 'websocket',
  initialState: {
    assets: [],
  },
  reducers: {
    storeAssetsList: (state, { payload }) => {
      state.assets = payload;
    },
  },
  // extraReducers: () => {
  // },
});

export const { storeAssetsList } = websocketSlice.actions;
export default websocketSlice.reducer;
