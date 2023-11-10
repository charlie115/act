import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  language: 'ko',
  theme: 'dark',
  timezone: 'Asia/Seoul',

  snackbar: {},
};

export const appSlice = createSlice({
  name: 'app',
  initialState,
  reducers: {
    changeLanguage: (state, { payload }) => {
      state.language = payload;
    },
    setSnackbar: (state, { payload }) => {
      state.snackbar = payload;
    },
    setTimezone: (state, { payload }) => {
      state.timezone = payload;
    },
    toggleTheme: (state, { payload }) => {
      state.theme = payload;
    },
  },
});

export const { changeLanguage, setSnackbar, setTimezone, toggleTheme } =
  appSlice.actions;

export default appSlice.reducer;
