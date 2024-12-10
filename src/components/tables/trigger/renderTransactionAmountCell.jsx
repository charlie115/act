import React from 'react';

import Typography from '@mui/material/Typography';

import formatIntlNumber from 'utils/formatIntlNumber';

export default function renderTradeCapitalCell({ cell }) {
  if (cell.getValue() === null) return '-';
  return <Typography>{formatIntlNumber(cell.getValue(), 2)}</Typography>;
}
