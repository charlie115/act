import React from 'react';

import Box from '@mui/material/Box';

import formatIntlNumber from 'utils/formatIntlNumber';

export default function renderFundingRateDiffCell({ cell }) {
  return (
    <Box sx={{ p: { xs: 0, md: 2 } }}>
      <Box sx={{ fontSize: { xs: 12, sm: 14 }, fontWeight: 700 }}>
        {formatIntlNumber(cell.getValue(), 4, 1)} <small>%</small>
      </Box>
    </Box>
  );
}
