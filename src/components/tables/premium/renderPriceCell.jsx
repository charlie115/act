import React from 'react';

import Box from '@mui/material/Box';
import Stack from '@mui/material/Stack';

import isUndefined from 'lodash/isUndefined';

import formatIntlNumber from 'utils/formatIntlNumber';

export default function renderPriceCell({ cell, row: { original } }) {
  return isUndefined(cell.getValue()) ? (
    '...'
  ) : (
    <>
      <Stack
        alignItems={{ xs: 'flex-start', sm: 'flex-end' }}
        direction={{ xs: 'column', sm: 'row' }}
        spacing={{ xs: 0, sm: 0.5 }}
      >
        <Box sx={{ fontSize: { xs: 9, sm: 12 } }}>
          {formatIntlNumber(cell.getValue(), 1)}
        </Box>
        <Box
          component="small"
          sx={{
            color: original.scr > 0 ? 'success.main' : 'error.main',
            fontWeight: 700,
          }}
        >
          {original.scr > 0 ? '+' : ''}
          {original.scr?.toFixed(2)}%
        </Box>
      </Stack>
      <Box>
        <Box component="small" sx={{ color: 'secondary.main' }}>
          {formatIntlNumber(original.converted_tp, 1)}
        </Box>
      </Box>
    </>
  );
}
