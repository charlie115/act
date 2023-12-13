import React from 'react';

import Box from '@mui/material/Box';

import formatIntlNumber from 'utils/formatIntlNumber';

import isUndefined from 'lodash/isUndefined';

export default function renderSpreadCell({ cell }) {
  return isUndefined(cell.getValue()) ? (
    '...'
  ) : (
    <>
      {cell.getValue() > 0 ? '+' : ''}
      {formatIntlNumber(cell.getValue(), 2, 1)}{' '}
      <Box component="small" sx={{ color: 'secondary.main' }}>
        %p
      </Box>
    </>
  );
}
