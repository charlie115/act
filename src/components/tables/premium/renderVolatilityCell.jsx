import React from 'react';

import Box from '@mui/material/Box';

import formatIntlNumber from 'utils/formatIntlNumber';

import isUndefined from 'lodash/isUndefined';

export default function renderVolatilityCell({ cell }) {
  const value = cell.getValue();

  return isUndefined(value) ? (
    '...'
  ) : (
    <Box
      component="span"
      sx={{
        fontSize: { xs: 10, sm: 12 },
        fontWeight: 400,
        color: value < 0 ? 'error.main' : 'inherit'
      }}
    >
      {formatIntlNumber(value, 5, 1)}
    </Box>
  );
}
