import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  language: 'ko',
  theme: 'dark',
};

export const appSlice = createSlice({
  name: 'app',
  initialState,
  reducers: {
    changeLanguage: (state, { payload }) => {
      state.language = payload;
    },
    toggleTheme: (state, { payload }) => {
      state.theme = payload;
    },
  },
});

export const { changeLanguage, toggleTheme } = appSlice.actions;

export default appSlice.reducer;
