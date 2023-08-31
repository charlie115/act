import React from 'react';

import { RouterProvider } from 'react-router-dom';

import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import GlobalStyles from '@mui/material/GlobalStyles';

import { useSelector } from 'react-redux';
import { useTranslation } from 'react-i18next';

import FullScreenLoading from 'components/FullScreenLoading';

import router from 'configs/router';
import theme, { darkTheme } from 'configs/theme';

import chartjs from 'configs/chartjs';

chartjs.init();

function App() {
  const { i18n } = useTranslation();

  const currentTheme = useSelector((state) => state.app.theme);

  if (!i18n.isInitialized) return null;

  return (
    <ThemeProvider theme={currentTheme === 'light' ? theme : darkTheme}>
      <CssBaseline />
      <GlobalStyles
        styles={{
          '::-webkit-scrollbar': {
            boxShadow: ' inset 0 0 6px rgba(49, 49, 49, 0.3)',
            borderRadius: '10px',
            height: 5,
            width: 4,
          },
          '::-webkit-scrollbar-thumb': {
            borderRadius: '10px',
            background: 'rgba(203, 227, 236, 0.4)',
            boxShadow: 'inset 0 0 6px rgba(#3c4b64, 0.5)',
          },
          '::-webkit-scrollbar-thumb:window-inactive': {
            background: 'rgba(203, 227, 236, 0.4)',
          },
          input: { textTransform: 'unset' },
        }}
      />
      <RouterProvider router={router} fallbackElement={<FullScreenLoading />} />
    </ThemeProvider>
  );
}

export default App;
