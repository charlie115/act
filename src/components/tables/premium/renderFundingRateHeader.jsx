import React from 'react';

import Box from '@mui/material/Box';
import Stack from '@mui/material/Stack';
import Tooltip from '@mui/material/Tooltip';

import i18n from 'configs/i18n';

import { MARKET_CODE_LIST } from 'constants/lists';

export default function renderFundingRateHeader({ column, marketCodes }) {
  const marketCode = MARKET_CODE_LIST.find(
    (o) =>
      o.value ===
      (column.id === 'targetFundingRate'
        ? marketCodes?.targetMarketCode
        : marketCodes?.originMarketCode)
  );
  if (!marketCode) return i18n.t('Funding Rate');
  return (
    <Tooltip
      title={marketCode.getLabel()}
      placement="bottom-end"
      sx={{ display: 'inline-flex' }}
    >
      <Stack
        useFlexGap
        alignItems="center"
        direction="row"
        flexWrap="wrap"
        spacing={0.5}
      >
        <Box component="span">{i18n.t('Funding Rate')}</Box>
        <Box
          component="img"
          src={marketCode.icon}
          alt={marketCode.label}
          sx={{
            height: { xs: 8, sm: 10, md: 12 },
            width: { xs: 8, sm: 10, md: 12 },
          }}
        />
      </Stack>
    </Tooltip>
  );
}
