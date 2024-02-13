import React from 'react';

import { DateTime } from 'luxon';

import isUndefined from 'lodash/isUndefined';

import FundingRate from 'components/FundingRate';

export default function renderFundingRateCell({ cell, column, row, table }) {
  const value = cell.getValue();
  if (isUndefined(value)) return '...';

  const fundingRate =
    column.id === 'targetFundingRate'
      ? row.original.targetFR
      : row.original.originFR;
  const dateTimeNow = fundingRate?.datetime_now
    ? DateTime.fromISO(fundingRate.datetime_now)
    : null;
  const fundingTime = fundingRate?.funding_time
    ? DateTime.fromISO(fundingRate.funding_time)
    : null;
  const diff =
    dateTimeNow && fundingTime
      ? fundingTime
          .diff(dateTimeNow, ['hours', 'minutes', 'seconds'])
          .toObject()
      : null;

  return (
    <FundingRate
      diff={diff}
      value={value}
      fundingTime={fundingRate?.funding_time}
      isMobile={table.options.meta.isMobile}
    />
  );
}
