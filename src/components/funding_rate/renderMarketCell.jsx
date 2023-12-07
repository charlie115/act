import React from 'react';

import Box from '@mui/material/Box';
import Stack from '@mui/material/Stack';

import { EXCHANGE_LIST } from 'constants/lists';

export default function renderMarketCell({ cell, row, isMobile }) {
  const value = cell.getValue();

  const exchange = EXCHANGE_LIST.find((o) => o.value === row.original.exchange);

  return (
    <Stack alignItems="center" direction="row" spacing={0.5} sx={{ pr: 1 }}>
      <Box
        component="img"
        src={exchange?.icon}
        alt={value}
        sx={{
          height: { xs: 8, sm: 10, md: 12 },
          width: { xs: 8, sm: 10, md: 12 },
        }}
      />
      <Box
        component="span"
        sx={{ fontSize: isMobile ? 10 : undefined, wordBreak: 'break-all' }}
      >
        {value}
      </Box>
    </Stack>
  );
}
