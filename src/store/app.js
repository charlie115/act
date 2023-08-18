import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  theme: 'dark',
};

export const appSlice = createSlice({
  name: 'app',
  initialState,
  reducers: {
    toggleTheme: (state, { payload }) => {
      state.theme = payload;
    },
  },
});

export const { toggleTheme } = appSlice.actions;

export default appSlice.reducer;
