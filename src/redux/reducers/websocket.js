import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  chat: { online: false },
  kline: { online: false },
};

export const websocketSlice = createSlice({
  name: 'websocket',
  initialState,
  reducers: {
    websocketConnected: (state, { payload }) => {
      state[payload].online = true;
    },
    websocketDisconnected: (state, { payload }) => {
      state[payload].online = false;
    },
  },
});

export const { websocketConnected, websocketDisconnected } =
  websocketSlice.actions;

export default websocketSlice.reducer;
