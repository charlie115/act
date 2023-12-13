import React from 'react';

import Box from '@mui/material/Box';

import { DateTime } from 'luxon';

import isUndefined from 'lodash/isUndefined';

import FundingRate from 'components/FundingRate';

export default function renderFundingRateCell({ cell, row, isMobile }) {
  const value = cell.getValue();

  if (isUndefined(value)) return '...';

  const diff = row.original.fundingTime
    ? DateTime.fromISO(row.original.fundingTime)
        .diff(DateTime.now(), ['hours', 'minutes', 'seconds'])
        .toObject()
    : null;

  return (
    <Box sx={{ py: 0.5 }}>
      <FundingRate
        diff={diff}
        value={value}
        decimal={5}
        fundingTime={row.original.fundingTime}
        isMobile={isMobile}
        sx={{ fontSize: { xs: 12, sm: 14 } }}
      />
    </Box>
  );
}
