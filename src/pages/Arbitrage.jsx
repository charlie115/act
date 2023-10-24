import React, { useMemo } from 'react';

import { useLocation } from 'react-router-dom';

import Box from '@mui/material/Box';

import ArbitrageTable from 'components/ArbitrageTable';

export default function Arbitrage() {
  const location = useLocation();

  return (
    <Box>
      <ArbitrageTable data={[]} />
    </Box>
  );
}
