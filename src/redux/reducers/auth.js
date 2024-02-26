import { createSlice } from '@reduxjs/toolkit';

import drfAuthApi from 'redux/api/drf/auth';

import { USER_ROLE } from 'constants';

const initialState = {
  user: null,
  id: null,
  loggedin: false,
  telegramBot: null,
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
          state.loggedin = payload.user.role !== USER_ROLE.visitor;
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
          state.loggedin = payload.role !== USER_ROLE.visitor;
          if (state.loggedin) {
            const telegramBot = payload?.socialapps?.find(
              (o) => o.provider === 'telegram'
            );
            state.telegramBot = telegramBot?.client_id;
          }
        }
      )
      .addMatcher(
        drfAuthApi.endpoints.userPatch.matchFulfilled,
        (state, { payload }) => {
          state.user = payload;
          const telegramBot = payload?.socialapps?.find(
            (o) => o.provider === 'telegram'
          );
          state.telegramBot = telegramBot?.client_id;
        }
      )
      .addMatcher(
        drfAuthApi.endpoints.userRegister.matchFulfilled,
        (state, { payload }) => {
          state.user = payload;
          state.loggedin = payload.role !== USER_ROLE.visitor;
          if (state.loggedin) {
            const telegramBot = payload?.socialapps?.find(
              (o) => o.provider === 'telegram'
            );
            state.telegramBot = telegramBot?.client_id;
          }
        }
      );
  },
});

export const { logout, newTokenReceived } = authSlice.actions;

export default authSlice.reducer;
