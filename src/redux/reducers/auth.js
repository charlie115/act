import { createSlice } from '@reduxjs/toolkit';
import jwtDecode from 'jwt-decode';
import drfApi from 'redux/api/drf';

const initialState = {
  accessToken: null,
  refreshToken: null,
  user: {},
};

export const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    logout: (state) => {
      state.accessToken = null;
      state.refreshToken = null;
      state.accessExpiration = null;
      state.refreshExpiration = null;
      state.user = {};
    },
  },
  extraReducers: (builder) => {
    builder.addMatcher(
      drfApi.endpoints.login.matchFulfilled,
      (state, { payload }) => {
        state.accessToken = payload.access;
        state.refreshToken = payload.refresh;
        console.log(jwtDecode(payload.access));
        state.user = payload.user;
      }
    );
  },
});

export const { login, logout } = authSlice.actions;

export default authSlice.reducer;
