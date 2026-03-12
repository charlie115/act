import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  chat: { active: false },
  kline: { active: false },
};

export const websocketSlice = createSlice({
  name: 'websocket',
  initialState,
  reducers: {
    websocketConnected: (state, { payload }) => {
      state[payload].active = true;
    },
    websocketDisconnected: (state, { payload }) => {
      state[payload].active = false;
    },
  },
});

export const { websocketConnected, websocketDisconnected } =
  websocketSlice.actions;

export default websocketSlice.reducer;
