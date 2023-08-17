import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  token: null,
  user: {},
};

export const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    signIn: (state) => {
      state.token = 1;
    },
    signOut: (state) => {
      state.token = null;
    },
  },
});

export const { signIn, signOut } = authSlice.actions;

export default authSlice.reducer;
