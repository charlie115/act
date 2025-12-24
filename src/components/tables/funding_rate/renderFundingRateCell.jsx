import React from 'react';

import Box from '@mui/material/Box';

import { DateTime } from 'luxon';

import isUndefined from 'lodash/isUndefined';

import FundingRate from 'components/FundingRate';

export default function renderFundingRateCell({ cell, row, isMobile }) {
  const value = cell.getValue();

  if (isUndefined(value)) return '...';

  const fundingTime = cell.column.getIsVisible()
    ? row.original.fundingTimeX
    : row.original.fundingTimeY;

  const fundingIntervalHours = cell.column.getIsVisible()
    ? row.original.funding_interval_hours_x
    : row.original.funding_interval_hours_y;

  const diff = fundingTime
    ? DateTime.fromISO(fundingTime)
        .diff(DateTime.now(), ['hours', 'minutes', 'seconds'])
        .toObject()
    : null;

  return (
    <Box sx={{ py: 0.5 }}>
      <FundingRate
        diff={diff}
        value={value}
        decimal={5}
        fundingTime={fundingTime}
        fundingIntervalHours={fundingIntervalHours}
        isMobile={isMobile}
        sx={{ fontSize: { xs: 12, sm: 14 } }}
      />
    </Box>
  );
}
