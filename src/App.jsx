import React, { useEffect } from 'react';

import { RouterProvider } from 'react-router-dom';

import { alpha, ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import GlobalStyles from '@mui/material/GlobalStyles';

import { useDispatch, useSelector } from 'react-redux';
import { setTimezone } from 'redux/reducers/app';

import { useTranslation } from 'react-i18next';

import { DateTime, Settings } from 'luxon';

import FullScreenLoading from 'components/FullScreenLoading';

import router from 'configs/router';
import theme, { darkTheme } from 'configs/theme';

function App() {
  const dispatch = useDispatch();

  const { i18n } = useTranslation();

  const appTheme = useSelector((state) => state.app.theme);

  const currentTheme = appTheme === 'light' ? theme : darkTheme;

  useEffect(() => {
    Settings.defaultZone = DateTime.local().zoneName;
    dispatch(setTimezone(Settings.defaultZone.zoneName));
  }, []);

  if (!i18n.isInitialized) return null;

  return (
    <ThemeProvider theme={currentTheme}>
      <CssBaseline />
      <GlobalStyles
        styles={{
          '::-webkit-scrollbar': {
            boxShadow: `inset 0 0 6px ${alpha(
              theme.palette.background.paper,
              0.1
            )}`,
            borderRadius: '10px',
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
          '#root': { minHeight: '100vh' },
        }}
      />
      <RouterProvider router={router} fallbackElement={<FullScreenLoading />} />
    </ThemeProvider>
  );
}

export default App;
