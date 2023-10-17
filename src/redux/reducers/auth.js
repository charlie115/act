import { createSlice } from '@reduxjs/toolkit';

import drfAuthApi from 'redux/api/drf/auth';
import drfChatApi from 'redux/api/drf/chat';

const initialState = {
  user: null,
  id: null,
  loggedin: false,
  nickname: null,
};

export const authSlice = createSlice({
  initialState,
  name: 'auth',
  reducers: {
    logout: (state) => {
      state.id = null;
      state.loggedin = false;
      state.user = null;
    },
    newTokenReceived: (state, { payload }) => {
      state.id.accessToken = payload.access;
    },
  },
  extraReducers: (builder) => {
    builder
      .addMatcher(
        drfAuthApi.endpoints.login.matchFulfilled,
        (state, { payload }) => {
          state.id = {
            accessToken: payload.access,
            refreshToken: payload.refresh,
          };
          state.user = payload.user;
          state.loggedin = payload.user.role !== 'visitor';
        }
      )
      .addMatcher(drfAuthApi.endpoints.logout.matchFulfilled, (state) => {
        state.id = null;
        state.loggedin = false;
        state.user = null;
      })
      .addMatcher(
        drfAuthApi.endpoints.user.matchFulfilled,
        (state, { payload }) => {
          state.user = payload;
          state.loggedin = payload.role !== 'visitor';
        }
      )
      .addMatcher(
        drfAuthApi.endpoints.userRegister.matchFulfilled,
        (state, { payload }) => {
          state.user = payload;
          state.loggedin = payload.role !== 'visitor';
        }
      )
      .addMatcher(
        drfChatApi.endpoints.getRandomUsername.matchFulfilled,
        (state, { payload }) => {
          state.nickname = payload;
        }
      );
  },
});

export const { logout, newTokenReceived } = authSlice.actions;

export default authSlice.reducer;
