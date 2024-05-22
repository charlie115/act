import React from 'react';

import Box from '@mui/material/Box';
import TopUpDeposit from 'components/TopUpDeposit';

export default function Deposit({ marketCodeCombination }) {
  const { tradeConfigUuid } = marketCodeCombination;

  return (
    <Box sx={{ p: 2 }}>
      <TopUpDeposit tradeConfigUuid={tradeConfigUuid} />
    </Box>
  );
}
