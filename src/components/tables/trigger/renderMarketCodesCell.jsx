import React from 'react';

import Box from '@mui/material/Box';

import SyncAltIcon from '@mui/icons-material/SyncAlt';

export default function renderMarketCodesCell({ cell }) {
  return (
    <Box sx={{ fontSize: 10, py: 0.5 }}>
      {cell.getValue().targetMarketCode}{' '}
      <SyncAltIcon color="accent" sx={{ fontSize: 10 }} />{' '}
      {cell.getValue().originMarketCode}
    </Box>
  );
}
