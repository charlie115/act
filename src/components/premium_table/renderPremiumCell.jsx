import React from 'react';

import Box from '@mui/material/Box';

import formatIntlNumber from 'utils/formatIntlNumber';

import isUndefined from 'lodash/isUndefined';

export default function renderPremiumCell({
  cell,
  row: { original },
  isTetherPriceView,
}) {
  if (isUndefined(cell.getValue())) return '...';
  return isTetherPriceView ? (
    <Box component="span" sx={{ fontWeight: 700 }}>
      {formatIntlNumber(original.dollar * (1 + cell.getValue() * 0.01), 2)}
    </Box>
  ) : (
    <>
      <Box
        component="span"
        sx={{ fontSize: { xs: 11, sm: 12 }, fontWeight: 700 }}
      >
        {formatIntlNumber(cell.getValue(), 3)}
      </Box>{' '}
      <small>%</small>
    </>
  );
}
