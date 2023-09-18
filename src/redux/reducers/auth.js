import { createSlice } from '@reduxjs/toolkit';

import drfApi from 'redux/api/drf';

const initialState = {
  accessToken: null,
  refreshToken: null,
  user: null,
  isAuthorized: false,
};

export const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    logout: (state) => {
      state.accessToken = null;
      state.refreshToken = null;
      state.isAuthorized = false;
      state.user = null;
    },
    newTokenReceived: (state, { payload }) => {
      state.accessToken = payload.access;
    },
  },
  extraReducers: (builder) => {
    builder
      .addMatcher(
        drfApi.endpoints.authLogin.matchFulfilled,
        (state, { payload }) => {
          state.accessToken = payload.access;
          state.refreshToken = payload.refresh;
          state.user = payload.user;
          state.isAuthorized = payload.user.role !== 'visitor';
        }
      )
      .addMatcher(drfApi.endpoints.authLogout.matchFulfilled, (state) => {
        state.accessToken = null;
        state.refreshToken = null;
        state.isAuthorized = false;
        state.user = null;
      })
      .addMatcher(
        drfApi.endpoints.authUserRegister.matchFulfilled,
        (state, { payload }) => {
          state.user = payload;
          state.isAuthorized = payload.role !== 'visitor';
        }
      );
  },
});

export const { logout, newTokenReceived } = authSlice.actions;

export default authSlice.reducer;
