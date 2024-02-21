import React from 'react';

import Box from '@mui/material/Box';

import i18n from 'configs/i18n';

export default function renderStatusCell({ cell }) {
  if (cell.getValue() === null) return '-';
  return (
    <Box
      component="small"
      sx={{ color: cell.getValue() ? 'success.main' : 'error.main' }}
    >
      {cell.getValue() ? i18n.t('Upward') : i18n.t('Downward')}
    </Box>
  );
}
