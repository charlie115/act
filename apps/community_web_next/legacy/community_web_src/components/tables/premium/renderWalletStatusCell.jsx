import React from 'react';

import Stack from '@mui/material/Stack';
import Tooltip from '@mui/material/Tooltip';

import ArrowRightAltIcon from '@mui/icons-material/ArrowRightAlt';

import { MARKET_CODE_LIST } from 'constants/lists';

export default function renderWalletStatusCell({ cell, table }) {
  const { marketCodes, isMobile } = table.options.meta;
  const targetMarketCode = MARKET_CODE_LIST.find(
    (o) => o.value === marketCodes?.targetMarketCode
  );
  const originMarketCode = MARKET_CODE_LIST.find(
    (o) => o.value === marketCodes?.originMarketCode
  );
  const walletStatus = cell.getValue();

  const iconSx = isMobile ? { fontSize: '0.625rem' } : { fontSize: '1rem' };
  const reverseIconSx = isMobile
    ? { fontSize: '0.625rem', transform: 'scaleX(-1)' }
    : { fontSize: '1rem', transform: 'scaleX(-1)' };

  if (!walletStatus) return '...';

  if (
    targetMarketCode.value.includes('SPOT') &&
    originMarketCode.value.includes('SPOT')
  )
    return (
      <Stack direction="column" spacing={-1}>
        <Tooltip
          placement="right"
          title={`${targetMarketCode.getLabel()} → ${originMarketCode.getLabel()}`}
        >
          <ArrowRightAltIcon
            color={walletStatus.right.length ? 'success' : 'error'}
            sx={iconSx}
          />
        </Tooltip>
        <Tooltip
          placement="right"
          title={`${targetMarketCode.getLabel()} ← ${originMarketCode.getLabel()}`}
        >
          <ArrowRightAltIcon
            color={walletStatus.left.length ? 'success' : 'error'}
            sx={reverseIconSx}
          />
        </Tooltip>
      </Stack>
    );

  return (
    <Stack direction="column" spacing={-1}>
      <ArrowRightAltIcon
        color={walletStatus.all.length ? 'success' : 'error'}
        sx={iconSx}
      />
      <ArrowRightAltIcon
        color={walletStatus.all.length ? 'success' : 'error'}
        sx={reverseIconSx}
      />
    </Stack>
  );
}
