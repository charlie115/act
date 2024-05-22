import React from 'react';

import Box from '@mui/material/Box';

import i18n from 'configs/i18n';

export default function renderStatusCell({ cell, row: { original } }) {
  if (original.trade_switch === -2)
    return (
      <Box component="small" sx={{ color: 'error.main' }}>
        {i18n.t('Entry Error')}
      </Box>
    );
  if (original.trade_switch === 2)
    return (
      <Box component="small" sx={{ color: 'error.main' }}>
        {i18n.t('Exit Error')}
      </Box>
    );

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
