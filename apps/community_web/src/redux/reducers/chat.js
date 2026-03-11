import { createSlice } from '@reduxjs/toolkit';

import drfChatApi from 'redux/api/drf/chat';

const initialState = {
  blocklist: [],
  enableNotification: true,
  nickname: null,
};

export const chatSlice = createSlice({
  name: 'chat',
  initialState,
  reducers: {
    blockUser: (state, { payload }) => {
      if (!state.blocklist.includes(payload)) state.blocklist.push(payload);
    },
    unblockUser: (state, { payload }) => {
      state.blocklist = state.blocklist.filter((item) => item !== payload);
    },
    toggleNotification: (state, { payload }) => {
      state.enableNotification = payload;
    },
  },
  extraReducers: (builder) => {
    builder.addMatcher(
      drfChatApi.endpoints.getRandomUsername.matchFulfilled,
      (state, { payload }) => {
        state.nickname = payload;
      }
    );
  },
});

export const { blockUser, unblockUser, toggleNotification } = chatSlice.actions;

export default chatSlice.reducer;
