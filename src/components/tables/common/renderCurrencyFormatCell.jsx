import React from 'react';

import Typography from '@mui/material/Typography';

import formatIntlNumber from 'utils/formatIntlNumber';

export default function renderCurrencyFormatCell({ cell }) {
  if (cell.getValue() === null) return '-';
  return <Typography>{formatIntlNumber(cell.getValue(), 2, 2)}</Typography>;
}
