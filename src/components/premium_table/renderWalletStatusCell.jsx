import React from 'react';

import Stack from '@mui/material/Stack';
import Tooltip from '@mui/material/Tooltip';

import ArrowRightAltIcon from '@mui/icons-material/ArrowRightAlt';

import { MARKET_CODE_LIST } from 'constants/lists';

export default function renderWalletStatusCell({ cell, marketCodes }) {
  const targetMarketCode = MARKET_CODE_LIST.find(
    (o) => o.value === marketCodes?.targetMarketCode
  );
  const originMarketCode = MARKET_CODE_LIST.find(
    (o) => o.value === marketCodes?.originMarketCode
  );
  const walletStatus = cell.getValue();

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
          />
        </Tooltip>
        <Tooltip
          placement="right"
          title={`${targetMarketCode.getLabel()} ← ${originMarketCode.getLabel()}`}
        >
          <ArrowRightAltIcon
            color={walletStatus.left.length ? 'success' : 'error'}
            sx={{ transform: 'scaleX(-1)' }}
          />
        </Tooltip>
      </Stack>
    );

  return (
    <Stack direction="column" spacing={-1}>
      <ArrowRightAltIcon
        color={walletStatus.all.length ? 'success' : 'error'}
      />
      <ArrowRightAltIcon
        color={walletStatus.all.length ? 'success' : 'error'}
        sx={{ transform: 'scaleX(-1)' }}
      />
    </Stack>
  );
}
