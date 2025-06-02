import React from 'react';

import Box from '@mui/material/Box';
import Tooltip from '@mui/material/Tooltip';
import SyncAltIcon from '@mui/icons-material/SyncAlt';

export default function renderMarketCodesCell({ cell, row, table }) {
  const marketCodes = cell.getValue();
  const targetMarketIcon = row.original?.targetMarketIcon;
  const originMarketIcon = row.original?.originMarketIcon;
  const isMobile = table.options.meta?.isMobile;

  const iconSize = isMobile ? '0.4rem' : '1rem';

  const targetCode = marketCodes?.targetMarketCode;
  const originCode = marketCodes?.originMarketCode;

  if (!targetCode || !originCode) {
    return '-';
  }

  return (
    <Box sx={{ py: 0.5, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 0.5 }}>
      {targetMarketIcon ? (
        <Tooltip title={targetCode} placement="top">
          <Box
            component="img"
            src={targetMarketIcon}
            alt={targetCode}
            sx={{ height: iconSize, width: iconSize }}
            onError={(e) => { e.target.style.display = 'none'; }}
          />
        </Tooltip>
      ) : (
        <Box sx={{ height: iconSize, width: iconSize }} />
      )}

      <SyncAltIcon color="accent" sx={{ fontSize: isMobile ? 6 : 10 }} />

      {originMarketIcon ? (
        <Tooltip title={originCode} placement="top">
          <Box
            component="img"
            src={originMarketIcon}
            alt={originCode}
            sx={{ height: iconSize, width: iconSize }}
            onError={(e) => { e.target.style.display = 'none'; }}
          />
        </Tooltip>
      ) : (
        <Box sx={{ height: iconSize, width: iconSize }} />
      )}
    </Box>
  );
}
