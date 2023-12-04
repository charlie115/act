import React from 'react';

import Box from '@mui/material/Box';
import Stack from '@mui/material/Stack';

import i18n from 'configs/i18n';

import { MARKET_CODE_LIST } from 'constants/lists';

export default function renderMarketCell({ cell, row }) {
  const value = cell.getValue();

  const marketCode = MARKET_CODE_LIST.find((o) => o.value === value);
  const similarExchange = MARKET_CODE_LIST.find(
    (o) => o.exchange === row.original.exchange
  );
  // return <div>{marketCode?.getLabel() || value}</div>;

  return (
    <Stack
      useFlexGap
      alignItems="center"
      direction="row"
      flexWrap="wrap"
      spacing={0.5}
    >
      <Box
        component="img"
        src={marketCode?.icon || similarExchange?.icon}
        alt={marketCode?.label || value}
        sx={{
          height: { xs: 8, sm: 10, md: 12 },
          width: { xs: 8, sm: 10, md: 12 },
        }}
      />
      <Box component="span">
        {marketCode?.getLabel() ||
          value
            .replace(/_/g, ' ')
            .replace(/(\/)(.*)/, ` (${row.original.quote_asset})`)}
      </Box>
    </Stack>
  );
}
