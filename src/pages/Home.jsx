import React from 'react';

import Box from '@mui/material/Box';

import { useTheme } from '@mui/material/styles';

import { useSelector } from 'react-redux';
import { useTranslation } from 'react-i18next';

import RealTimePremiumTable from 'components/RealTimePremiumTable';

function Home() {
  const { i18n, t } = useTranslation();

  const theme = useTheme();

  const { timezone } = useSelector((state) => state.app);
  const { loggedin, user } = useSelector((state) => state.auth);

  return (
    <Box sx={{ overflowX: 'hidden', p: 1 }}>
      <RealTimePremiumTable
        t={t}
        language={i18n.language}
        loggedin={loggedin}
        theme={theme}
        timezone={timezone}
        user={user}
      />
    </Box>
  );
}

export default Home;
