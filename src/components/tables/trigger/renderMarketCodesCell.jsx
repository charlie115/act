import React from 'react';

import Box from '@mui/material/Box';
import Tooltip from '@mui/material/Tooltip';
import SyncAltIcon from '@mui/icons-material/SyncAlt';

export default function renderMarketCodesCell({ cell, row, table }) {
  const marketCodes = cell.getValue();
  const { targetMarketIcon, originMarketIcon } = row.original;
  const isMobile = table.options.meta?.isMobile;

  const iconSize = isMobile ? '0.6rem' : '1rem';

  return (
    <Box sx={{ py: 0.5, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 0.5 }}>
      <Tooltip title={marketCodes.targetMarketCode} placement="top">
        <Box
          component="img"
          src={targetMarketIcon}
          alt={marketCodes.targetMarketCode}
          sx={{ height: iconSize, width: iconSize }}
        />
      </Tooltip>

      <SyncAltIcon color="accent" sx={{ fontSize: isMobile ? 8 : 10 }} />

      <Tooltip title={marketCodes.originMarketCode} placement="top">
        <Box
          component="img"
          src={originMarketIcon}
          alt={marketCodes.originMarketCode}
          sx={{ height: iconSize, width: iconSize }}
        />
      </Tooltip>
    </Box>
  );
}
