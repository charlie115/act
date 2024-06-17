import React from 'react';

import Box from '@mui/material/Box';

import { DateTime } from 'luxon';

import isUndefined from 'lodash/isUndefined';

import FundingRate from 'components/FundingRate';

import i18n from 'configs/i18n';

export default function renderFundingRateCell({ cell, column, row, table }) {
  const value = cell.getValue();
  if (isUndefined(value)) return '...';
  if (value === null)
    return (
      <Box sx={{ color: 'secondary.main', fontSize: 10 }}>{i18n.t('NONE')}</Box>
    );

  const { isMobile } = table.options.meta;

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

  const label =
    column.id === 'targetFundingRate'
      ? row.original.marketCodes?.targetMarketCode
      : row.original.marketCodes?.originMarketCode;
  const icon =
    column.id === 'targetFundingRate'
      ? row.original.targetFundingRateIcon
      : row.original.originFundingRateIcon;

  return (
    <>
      {icon && (
        <Box
          component="img"
          src={icon}
          alt={label}
          sx={{
            mr: 1,
            height: { xs: 8, sm: 10, md: 12 },
            width: { xs: 8, sm: 10, md: 12 },
          }}
        />
      )}
      <FundingRate
        diff={diff}
        value={value}
        fundingTime={fundingRate?.funding_time}
        isMobile={isMobile}
      />
    </>
  );
}
