import React from 'react';

import Box from '@mui/material/Box';

import i18n from 'configs/i18n';

import ExitToAppIcon from '@mui/icons-material/ExitToApp';

export default function renderStatusCell({ cell, row: { original }, table }) {
  const { betweenFutures } = table.options.meta || {};

  if (original.trade_capital === null) {
    let color;
    let text;

    if (original.trigger_switch === 1) {
      color = 'success.light';
      text = i18n.t('Upward');
    } else if (original.trigger_switch === 0) {
      color = 'error.light';
      text = i18n.t('Downward');
    } else {
      color = 'warning.light';
      text = i18n.t('Wait');
    }
  
    return (
      <Box
        component="small"
        sx={{ color }}
      >
        {text}
      </Box>
    );
  }

  if (cell.getValue() === null) return '-';

  if (cell.getValue() === 3)
    return (
      <Box component="small" sx={{ color: 'success.main' }}>
        {i18n.t('Transaction in Progress')}
      </Box>
    );

  if (betweenFutures) {
    if (cell.getValue() === -2)
      return (
        <Box component="small" sx={{ color: 'error.main' }}>
          {original.trigger_switch === 1
            ? i18n.t('Downward Entry Error')
            : i18n.t('Upward Entry Error')}
        </Box>
      );
    if (cell.getValue() === -1)
      return (
        <Box component="small" sx={{ color: 'warning.main' }}>
          {original.trigger_switch === 1
            ? i18n.t('Waiting for Downward Exit')
            : i18n.t('Waiting for Upward Exit')}
          <ExitToAppIcon sx={{ fontSize: 'inherit', marginLeft: 0.5, mt: 1 }} />
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
          {original.trigger_switch === 1
            ? i18n.t('Upward Exit Complete')
            : i18n.t('Downward Exit Complete')}
        </Box>
      );
    if (cell.getValue() === 2)
      return (
        <Box component="small" sx={{ color: 'error.main' }}>
          {original.trigger_switch === 1
            ? i18n.t('Upward Exit Error')
            : i18n.t('Downward Exit Error')}
        </Box>
      );
  } else {
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
          <ExitToAppIcon sx={{ fontSize: 'inherit', marginLeft: 0.5, mt: 1 }} />
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
  }
  
  return null;
}
