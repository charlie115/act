import React, { useEffect } from 'react';

import { RouterProvider } from 'react-router-dom';

import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import GlobalStyles from '@mui/material/GlobalStyles';

import { LocalizationProvider } from '@mui/x-date-pickers';

import { useDispatch, useSelector } from 'react-redux';
import { setTimezone } from 'redux/reducers/app';

import { useTranslation } from 'react-i18next';

import { DateTime, Settings } from 'luxon';
import { AdapterLuxon } from '@mui/x-date-pickers/AdapterLuxon';

import FullScreenLoading from 'components/FullScreenLoading';

import router from 'configs/router';
import theme, { darkTheme } from 'configs/theme';

import useCookie from 'hooks/useCookie';

function App() {
  const dispatch = useDispatch();

  const { i18n } = useTranslation();

  const appTheme = useSelector((state) => state.app.theme);
  const { loggedin } = useSelector((state) => state.auth);

  const currentTheme = appTheme === 'light' ? theme : darkTheme;

  const { clearCookie: clearDepositAddress } = useCookie('dpaddr');

  const { clearCookie: clearCountdown } = useCookie('dpcntdwn');

  useEffect(() => {
    const localZone = DateTime.local().zoneName;
    Settings.defaultZone = localZone;
    dispatch(setTimezone(localZone));
  }, [dispatch]);

  useEffect(() => {
    if (!loggedin) {
      clearDepositAddress();
      clearCountdown();
    }
  }, []);

  if (!i18n.isInitialized) return null;

  return (
    <LocalizationProvider dateAdapter={AdapterLuxon}>
      <ThemeProvider theme={currentTheme}>
        <CssBaseline />
        <GlobalStyles
          styles={{
            input: { textTransform: 'unset' },
            '#root': { height: '100vh', overflowY: 'hidden' },
            '*, html': {
              scrollBehavior: 'smooth !important',
              '::-webkit-scrollbar': {
                borderRadius: '10px',
                scrollbarWidth: 'thin',
                width: 4,
              },
              '::-webkit-scrollbar-thumb': {
                borderRadius: '10px',
                background: 'rgba(203, 227, 236, 0.2)',
              },
              '::-webkit-scrollbar-thumb:window-inactive': {
                opacity: 0,
              },
              '.show-more-or-less': {
                color: '#64748b',
                cursor: 'pointer',
                fontSize: 12,
                // display: 'block',
              },
            },
          }}
        />
        <RouterProvider
          router={router}
          fallbackElement={<FullScreenLoading />}
        />
      </ThemeProvider>
    </LocalizationProvider>
  );
}

export default App;
