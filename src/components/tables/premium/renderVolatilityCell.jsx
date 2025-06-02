import React from 'react';

import Box from '@mui/material/Box';

import formatIntlNumber from 'utils/formatIntlNumber';

import isUndefined from 'lodash/isUndefined';

export default function renderVolatilityCell({ cell }) {
  return isUndefined(cell.getValue()) ? (
    '...'
  ) : (
    <Box
      component="span"
      sx={{ fontSize: { xs: 10, sm: 12 }, fontWeight: 400 }}
    >
      {formatIntlNumber(cell.getValue(), 5, 1)}
    </Box>
  );
}
