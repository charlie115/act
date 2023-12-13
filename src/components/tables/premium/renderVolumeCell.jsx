import React from 'react';

import Box from '@mui/material/Box';

import isUndefined from 'lodash/isUndefined';

import formatShortNumber from 'utils/formatShortNumber';

export default function renderVolumeCell({ cell }) {
  return isUndefined(cell.getValue()) ? (
    '...'
  ) : (
    <Box sx={{ fontSize: { xs: 10, sm: 12 } }}>
      {formatShortNumber(cell.getValue(), 2)}
    </Box>
  );
}
