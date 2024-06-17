import React from 'react';

import Box from '@mui/material/Box';

import i18n from 'configs/i18n';

export default function renderStatusCell({ cell, row: { original } }) {
  if (original.trade_capital === null)
    return (
      <Box
        component="small"
        sx={{
          color: original.trigger_switch ? 'success.light' : 'error.light',
        }}
      >
        {original.trigger_switch ? i18n.t('Upward') : i18n.t('Downward')}
      </Box>
    );

  if (cell.getValue() === null) return '-';

  if (cell.getValue() === -2)
    return (
      <Box component="small" sx={{ color: 'error.main' }}>
        {i18n.t('Entry Error')}
      </Box>
    );
  if (cell.getValue() === -1)
    return (
      <Box component="small" sx={{ color: 'warning.main' }}>
        {i18n.t('Waiting for Exit')}
      </Box>
    );
  if (cell.getValue() === 0)
    return (
      <Box component="small" sx={{ color: 'warning.main' }}>
        {i18n.t('Waiting for Entry')}
      </Box>
    );
  if (cell.getValue() === 1)
    return (
      <Box component="small" sx={{ color: 'info.main' }}>
        {i18n.t('Exit Complete')}
      </Box>
    );
  if (cell.getValue() === 2)
    return (
      <Box component="small" sx={{ color: 'error.main' }}>
        {i18n.t('Exit Error')}
      </Box>
    );
  if (cell.getValue() === 3)
    return (
      <Box component="small" sx={{ color: 'success.main' }}>
        {i18n.t('Transaction in Progress')}
      </Box>
    );

  return null;
}
