import { createSlice } from '@reduxjs/toolkit';

import drfApi from 'redux/api/drf';

const initialState = {
  user: null,
  id: null,
  loggedin: false,
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
        drfApi.endpoints.authLogin.matchFulfilled,
        (state, { payload }) => {
          state.id = {
            accessToken: payload.access,
            refreshToken: payload.refresh,
          };
          state.user = payload.user;
          state.loggedin = payload.user.role !== 'visitor';
        }
      )
      .addMatcher(drfApi.endpoints.authLogout.matchFulfilled, (state) => {
        state.id = null;
        state.loggedin = false;
        state.user = null;
      })
      .addMatcher(
        drfApi.endpoints.authUser.matchFulfilled,
        (state, { payload }) => {
          state.user = payload;
          state.loggedin = payload.role !== 'visitor';
        }
      )
      .addMatcher(
        drfApi.endpoints.authUserRegister.matchFulfilled,
        (state, { payload }) => {
          state.user = payload;
          state.loggedin = payload.role !== 'visitor';
        }
      );
  },
});

export const { logout, newTokenReceived } = authSlice.actions;

export default authSlice.reducer;
