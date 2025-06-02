import React from 'react';

import Box from '@mui/material/Box';

import formatIntlNumber from 'utils/formatIntlNumber';

import isUndefined from 'lodash/isUndefined';

export default function renderPremiumCell({ cell, row: { original }, table }) {
  if (isUndefined(cell.getValue())) return '...';
  const { isMobile, isTetherPriceView } = table.options.meta;
  
  return isTetherPriceView ? (
    <Box component="span" sx={{ fontSize: { xs: 8, sm: 12 }, fontWeight: { xs: 400, sm: 700 } }}>
      {formatIntlNumber(
        original.dollar * (1 + cell.getValue() * 0.01), 
        isMobile ? 1 : 2
      )}
    </Box>
  ) : (
    <>
      <Box
        component="span"
        sx={{ fontSize: { xs: 10, sm: 12 }, fontWeight: { xs: 400, sm: 700 } }}
      >
        {formatIntlNumber(cell.getValue(), isMobile ? 2 : 3)}
      </Box>{' '}      
    </>
  );
}
