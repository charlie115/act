import React from 'react';

import Box from '@mui/material/Box';

import i18n from 'configs/i18n';

import ExitToAppIcon from '@mui/icons-material/ExitToApp';

export default function renderStatusCell({ cell, row: { original }, table }) {
  const { betweenFutures, isMobile } = table.options.meta || {};

  // Helper function for consistent styling
  function StatusBox({ color, children }) {
    return (
      <Box component="small" sx={{ 
        color,
        fontSize: isMobile ? '0.4rem' : 'inherit'
      }}>
        {children}
      </Box>
    );
  }

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
  
    return <StatusBox color={color}>{text}</StatusBox>;
  }

  if (cell.getValue() === null) return '-';

  if (cell.getValue() === 3)
    return <StatusBox color="success.main">{i18n.t('Transaction in Progress')}</StatusBox>;

  if (betweenFutures) {
    if (cell.getValue() === -2)
      return (
        <StatusBox color="error.main">
          {original.trigger_switch === 1
            ? i18n.t('Downward Entry Error')
            : i18n.t('Upward Entry Error')}
        </StatusBox>
      );
    if (cell.getValue() === -1)
      return (
        <StatusBox color="warning.main">
          {original.trigger_switch === 1
            ? i18n.t('Waiting for Downward Exit')
            : i18n.t('Waiting for Upward Exit')}
          <ExitToAppIcon sx={{ fontSize: 'inherit', marginLeft: 0.5, mt: 1 }} />
        </StatusBox>
      );
    if (cell.getValue() === 0)
      return <StatusBox color="warning.main">{i18n.t('Waiting for Entry')}</StatusBox>;
    if (cell.getValue() === 1)
      return (
        <StatusBox color="info.main">
          {original.trigger_switch === 1
            ? i18n.t('Upward Exit Complete')
            : i18n.t('Downward Exit Complete')}
        </StatusBox>
      );
    if (cell.getValue() === 2)
      return (
        <StatusBox color="error.main">
          {original.trigger_switch === 1
            ? i18n.t('Upward Exit Error')
            : i18n.t('Downward Exit Error')}
        </StatusBox>
      );
  } else {
    if (cell.getValue() === -2)
      return <StatusBox color="error.main">{i18n.t('Entry Error')}</StatusBox>;
    if (cell.getValue() === -1)
      return (
        <StatusBox color="warning.main">
          {i18n.t('Waiting for Exit')}
          <ExitToAppIcon sx={{ fontSize: 'inherit', marginLeft: 0.5, mt: 1 }} />
        </StatusBox>
      );
    if (cell.getValue() === 0)
      return <StatusBox color="warning.main">{i18n.t('Waiting for Entry')}</StatusBox>;
    if (cell.getValue() === 1)
      return <StatusBox color="info.main">{i18n.t('Exit Complete')}</StatusBox>;
    if (cell.getValue() === 2)
      return <StatusBox color="error.main">{i18n.t('Exit Error')}</StatusBox>;
  }
  
  return null;
}
