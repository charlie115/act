import React from 'react';

import Typography from '@mui/material/Typography';

import formatIntlNumber from 'utils/formatIntlNumber';

export default function renderCurrencyFormatCell({ cell, table }) {
  const isMobile = table.options.meta?.isMobile;

  if (cell.getValue() === null) return '-';
  return (
    <Typography sx={{ fontSize: isMobile ? '0.4rem !important' : 'inherit' }}>
      {formatIntlNumber(cell.getValue(), 2)}
    </Typography>
  );
}
