import React from 'react';

import Typography from '@mui/material/Typography';

import { DEPOSIT_TYPE } from 'constants';

export default function renderDepositTypeCell({ cell }) {
  const value = DEPOSIT_TYPE[cell.getValue()];
  if (!value) return '-';
  return (
    <Typography
      sx={{ color: value?.color, fontWeight: 700, textTransform: 'uppercase' }}
    >
      {value?.getLabel()}
    </Typography>
  );
}
