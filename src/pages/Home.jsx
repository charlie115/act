import React from 'react';

import Box from '@mui/material/Box';

import { useTheme } from '@mui/material/styles';
import useMediaQuery from '@mui/material/useMediaQuery';

import { useSelector } from 'react-redux';
import { useTranslation } from 'react-i18next';

import RealTimePremiumTable from 'components/RealTimePremiumTable';

function Home() {
  const { i18n, t } = useTranslation();

  const theme = useTheme();

  const matchLargeScreen = useMediaQuery('(min-width:600px)');

  const { timezone } = useSelector((state) => state.app);
  const { loggedin } = useSelector((state) => state.auth);

  return (
    <Box>
      <RealTimePremiumTable
        t={t}
        language={i18n.language}
        loggedin={loggedin}
        theme={theme}
        timezone={timezone}
        matchLargeScreen={matchLargeScreen}
      />
    </Box>
  );
}

export default Home;
