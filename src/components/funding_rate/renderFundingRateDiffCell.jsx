import React from 'react';

import Box from '@mui/material/Box';

import formatIntlNumber from 'utils/formatIntlNumber';

export default function renderFundingRateDiffCell({ cell }) {
  return (
    <Box sx={{ p: 2 }}>
      <Box sx={{ fontSize: 14, fontWeight: 700 }}>
        {formatIntlNumber(cell.getValue(), 4, 1)} <small>%</small>
      </Box>
    </Box>
  );
}
