import React from 'react';

import Box from '@mui/material/Box';

import formatIntlNumber from 'utils/formatIntlNumber';

import isUndefined from 'lodash/isUndefined';

export default function renderSpreadCell({ cell }) {
  return isUndefined(cell.getValue()) ? (
    '...'
  ) : (
    <>
      <Box
        component="span"
        sx={{ fontSize: { xs: 10, sm: 12 }, fontWeight: 400 }}
      >
        {cell.getValue() > 0 ? '+' : ''}
        {formatIntlNumber(cell.getValue(), 2, 1)}
      </Box>{' '}
      <Box component="small" sx={{ color: 'secondary.main' }}>
        %p
      </Box>
    </>
  );
}
