import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  theme: 'dark',
};

export const authSlice = createSlice({
  name: 'app',
  initialState,
  reducers: {
    changeTheme: (state, { payload }) => {
      state.theme = payload;
    },
  },
});

export const { signIn, signOut } = authSlice.actions;

export default authSlice.reducer;
